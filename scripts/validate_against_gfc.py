"""Command-line validation of ForestWatch candidate events against GFC."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rasterio.coords import BoundingBox

from forestwatch.schemas.events import ForestEvent
from forestwatch.validation.gfc import (
    GFCValidationRecord,
    summarize_records,
    validate_event_bounds,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ForestWatch detections against a Hansen GFC lossyear raster."
    )
    parser.add_argument(
        "--detections",
        type=Path,
        required=True,
        help="JSON artifact containing candidate_events with typed geospatial bounds.",
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
        "--loss-threshold",
        type=int,
        default=1,
        help="Minimum GFC lossyear value treated as loss evidence (1..24).",
    )
    return parser.parse_args()


def load_candidate_events(path: Path) -> list[ForestEvent]:
    """Load and validate candidate events from the Phase 5 JSON contract."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")

    raw_events = payload.get("candidate_events", [])
    if not isinstance(raw_events, list):
        raise ValueError("Detections artifact must contain a candidate_events list.")

    events: list[ForestEvent] = []
    for record in raw_events:
        if not isinstance(record, dict):
            continue
        raw_event = record.get("event")
        if isinstance(raw_event, dict):
            events.append(ForestEvent.model_validate(raw_event))
    return events


def main() -> int:
    args = parse_args()
    detections = args.detections.expanduser().resolve()
    gfc = args.gfc.expanduser().resolve()

    if not detections.is_file():
        raise FileNotFoundError(f"Detections artifact not found: {detections}")
    if not gfc.is_file():
        raise FileNotFoundError(f"GFC raster not found: {gfc}")

    events = load_candidate_events(detections)
    records: list[GFCValidationRecord] = []

    for event in events:
        if event.bounds is None:
            raise ValueError(
                f"Event {event.event_id} has no geospatial bounds. "
                "Phase 8 refuses to infer raster geometry from latitude/longitude alone."
            )

        bounds = BoundingBox(
            event.bounds.left,
            event.bounds.bottom,
            event.bounds.right,
            event.bounds.top,
        )
        records.append(
            validate_event_bounds(
                event_id=event.event_id,
                bounds=bounds,
                bounds_crs=event.bounds.crs,
                dataset_path=gfc,
                threshold=args.loss_threshold,
            )
        )

    summary = summarize_records(records)
    output = {
        "detections_artifact": str(detections),
        "gfc_raster": str(gfc),
        "candidate_count": summary.candidate_count,
        "comparable_count": summary.comparable_count,
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
                "valid_pixels": record.valid_pixels,
                "loss_pixels": record.loss_pixels,
                "overlaps_raster": record.overlaps_raster,
            }
            for record in summary.records
        ],
    }

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Candidate events: {summary.candidate_count}")
    print(f"Comparable events: {summary.comparable_count}")
    print(f"GFC agreement rate: {summary.agreement_rate:.4f}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
