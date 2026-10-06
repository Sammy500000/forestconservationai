"""Run the Phase 5 end-to-end ForestWatch demonstration."""
from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import torch

from forestwatch.config import load_yaml_config
from forestwatch.detection.pipeline import run_detection
from forestwatch.ml.constants import EUROSAT_CHECKPOINT_CLASSES
from forestwatch.ml.model import build_resnet50, load_eurosat_checkpoint
from forestwatch.networking.integration import deliver_in_memory_concurrently
from forestwatch.networking.priority import PriorityEventQueue
from forestwatch.networking.router import PriorityRouter
from forestwatch.networking.topology import build_default_topology
from forestwatch.schemas.events import AlertPriority, EventType, ForestEvent

RECIPIENTS: tuple[str, ...] = ("node_a", "district", "control_room")


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but unavailable.")
    return torch.device(requested)


def priority_for_confidence(confidence: float) -> AlertPriority:
    if confidence >= 0.90:
        return AlertPriority.CRITICAL
    if confidence >= 0.80:
        return AlertPriority.HIGH
    if confidence >= 0.70:
        return AlertPriority.MEDIUM
    return AlertPriority.LOW


def _sum_confusion(results: list[dict[str, object]]) -> dict[str, int]:
    total = {"tn": 0, "fp": 0, "fn": 0, "tp": 0}
    for result in results:
        matrix = result["confusion_matrix"]
        for key in total:
            total[key] += int(matrix[key])
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ForestWatch Phase 5 end-to-end demo.")
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("data/external/forest_change"),
    )
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--confidence-threshold", type=float, default=None)
    parser.add_argument("--ground-truth-threshold", type=float, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/metrics/phase5_demo.json"),
    )
    args = parser.parse_args()

    if args.limit <= 0:
        raise ValueError("--limit must be positive")

    detection_config = load_yaml_config("detection.yaml")["detection"]
    confidence_threshold = (
        float(args.confidence_threshold)
        if args.confidence_threshold is not None
        else float(detection_config["confidence_threshold"])
    )
    ground_truth_threshold = (
        float(args.ground_truth_threshold)
        if args.ground_truth_threshold is not None
        else float(detection_config.get("ground_truth_threshold", 0.10))
    )
    patch_size = int(detection_config["patch_size_pixels"])

    device = choose_device(args.device)
    model = build_resnet50(num_classes=len(EUROSAT_CHECKPOINT_CLASSES))
    model = load_eurosat_checkpoint(model).to(device).eval()

    detection_started = time.perf_counter()
    detection = run_detection(
        model,
        args.dataset_root,
        split=args.split,
        device=device,
        patch_size=patch_size,
        confidence_threshold=confidence_threshold,
        ground_truth_threshold=ground_truth_threshold,
        limit=args.limit,
    )
    detection_seconds = time.perf_counter() - detection_started

    router = PriorityRouter(build_default_topology())
    queue = PriorityEventQueue()
    event_records: list[dict[str, object]] = []

    for example in detection["examples"]:
        sample_id = str(example["sample_id"])
        for index, candidate in enumerate(example["candidates"]):
            confidence = float(candidate["confidence"])
            event = ForestEvent(
                event_id=f"PHASE5-{sample_id}-{index + 1:04d}",
                event_type=EventType.FOREST_LOSS_CANDIDATE,
                priority=priority_for_confidence(confidence),
                confidence=confidence,
                location={"latitude": 0.0, "longitude": 0.0},
                detected_at=datetime.now(UTC),
                before_class=str(candidate["before_class"]),
                after_class=str(candidate["after_class"]),
                sample_id=sample_id,
                patch_row=int(candidate["row"]),
                patch_column=int(candidate["column"]),
            )
            queue.put(event)

    ordered_event_ids: list[str] = []
    while not queue.is_empty():
        event = queue.get()
        ordered_event_ids.append(event.event_id)
        notification_started = time.perf_counter()
        notifications = deliver_in_memory_concurrently(
            event,
            recipients=RECIPIENTS,
            router=router,
        )
        notification_latency_ms = (time.perf_counter() - notification_started) * 1000
        event_records.append(
            {
                "event": event.model_dump(mode="json"),
                "notifications": [
                    {
                        "recipient": notification.recipient,
                        "path": list(notification.path),
                        "path_cost": notification.path_cost,
                        "delivered_at": notification.delivered_at.isoformat(),
                    }
                    for notification in notifications
                ],
                "notification_latency_ms": notification_latency_ms,
            }
        )

    confusion = _sum_confusion([dict(result) for result in detection["examples"]])
    tp = confusion["tp"]
    fp = confusion["fp"]
    fn = confusion["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    output = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_root": str(args.dataset_root),
        "split": args.split,
        "device": str(device),
        "limit": args.limit,
        "confidence_threshold": confidence_threshold,
        "ground_truth_threshold": ground_truth_threshold,
        "patch_size": patch_size,
        "detection_seconds": detection_seconds,
        "ordered_event_ids": ordered_event_ids,
        "detection_summary": {
            "example_count": detection["example_count"],
            "patch_count": detection["patch_count"],
            "candidate_count": detection["candidate_count"],
            "confusion_matrix": confusion,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "examples": detection["examples"],
        "candidate_events": event_records,
    }
    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("Phase 5 end-to-end demo completed.")
    print(f"Examples: {detection['example_count']}")
    print(f"Candidates: {detection['candidate_count']}")
    print(f"Detection F1 (patch-level): {f1:.4f}")
    print(f"Priority-ordered events: {len(ordered_event_ids)}")
    if event_records:
        first = event_records[0]
        first_notification = first["notifications"][0]
        print(f"First route: {' -> '.join(first_notification['path'])}")
        print(f"First route cost: {first_notification['path_cost']}")
        print(f"Recipients: {len(first['notifications'])}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
