"""Command-line validation of ForestWatch candidate patches against GFC."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rasterio.coords import BoundingBox

from forestwatch.validation.gfc import GFCValidationRecord, summarize_records, validate_event_bounds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ForestWatch detections against a Hansen GFC lossyear raster."
    )
    parser.add_argument(
        "--detections",
        type=Path,
        required=True,
        help="JSON artifact containing candidate events.",
    )
    parser.add_argument(
        "--gfc",
        type=Path,
        required=True,
        help="Local Hansen GFC lossyear GeoTIFF.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/metrics/phase8_gfc_validation.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--pixel-size-meters",
        type=float,
        default=640.0,
        help="Patch side length used when detections are grid coordinates rather than bounds.",
    )
    parser.add_argument(
        "--loss-threshold",
        type=int,
        default=1,
        help="Minimum non-zero GFC lossyear value treated as loss evidence.",
    )
    return parser.parse_args()


def load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    events = payload.get("candidate_events", [])
    if not isinstance(events, list):
        raise ValueError("Detections artifact must contain a candidate_events list.")

    candidates: list[dict[str, Any]] = []
    for record in events:
        if not isinstance(record, dict):
            continue
        event = record.get("event")
        if isinstance(event, dict):
            candidates.append(event)
    return candidates


def event_bounds(event: dict[str, Any], *, pixel_size: float) -> BoundingBox:
    bounds = event.get("bounds")
    if isinstance(bounds, dict):
        return BoundingBox(
            float(bounds["left"]),
            float(bounds["bottom"]),
            float(bounds["right"]),
            float(bounds["top"]),
        )

    location = event.get("location")
    if not isinstance(location, dict):
        raise ValueError(
            f"Event {event.get('event_id', '<unknown>')} has neither bounds nor location."
        )

    latitude = float(location["latitude"])
    longitude = float(location["longitude"])

    # Location-only events are not projectable to a GFC raster without a CRS transform.
    # Keep the CLI explicit rather than silently inventing a geographic bounding box.
    raise ValueError(
        f"Event {event.get('event_id', '<unknown>')} contains only latitude/longitude. "
        "Phase 8 requires geospatial bounds in the event artifact (or a future CRS-aware adapter)."
    )


def main() -> int:
    args = parse_args()
    detections = args.detections.expanduser().resolve()
    gfc = args.gfc.expanduser().resolve()

    if not detections.is_file():
        raise FileNotFoundError(f"Detections artifact not found: {detections}")
    if not gfc.is_file():
        raise FileNotFoundError(f"GFC raster not found: {gfc}")

    candidates = load_candidates(detections)
    records: list[GFCValidationRecord] = []

    for event in candidates:
        event_id = str(event["event_id"])
        bounds = event_bounds(event, pixel_size=args.pixel_size_meters)
        records.append(
            validate_event_bounds(
                event_id=event_id,
                bounds=bounds,
                dataset_path=gfc,
                threshold=args.loss_threshold,
            )
        )

    summary = summarize_records(records)
    output = {
        "detections_artifact": str(detections),
        "gfc_raster": str(gfc),
        "candidate_count": summary.candidate_count,
        "candidates_with_gfc_loss": summary.candidates_with_loss,
        "agreement_rate": summary.agreement_rate,
        "mean_loss_fraction": summary.mean_loss_fraction,
        "records": [
            {
                "event_id": record.event_id,
                "loss_fraction": record.loss_fraction,
                "has_loss": record.has_loss,
                "min_loss_year": record.min_loss_year,
                "max_loss_year": record.max_loss_year,
            }
            for record in summary.records
        ],
    }

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Validated {summary.candidate_count} candidate events.")
    print(f"GFC agreement rate: {summary.agreement_rate:.4f}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
