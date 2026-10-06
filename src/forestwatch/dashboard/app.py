"""Minimal Streamlit dashboard for generated ForestWatch artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image, ImageDraw

DEFAULT_METRICS = Path("artifacts/metrics/eurosat_metrics.json")
DEFAULT_PHASE5 = Path("artifacts/metrics/phase5_demo.json")
DEFAULT_DATASET = Path("data/external/forest_change")


def _load_json(path: Path) -> dict[str, Any] | None:
    """Load a generated JSON artifact, returning None when it is unavailable."""
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def _prediction_mask(
    example: dict[str, Any], image_size: tuple[int, int], patch_size: int
) -> Image.Image:
    """Build a display-only patch mask from the recorded Phase 5 candidates."""
    width, height = image_size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    for patch in example.get("patches", []):
        if not patch.get("candidate", False):
            continue
        row = int(patch["row"])
        column = int(patch["column"])
        left = column * patch_size
        top = row * patch_size
        draw.rectangle(
            (left, top, min(left + patch_size, width) - 1, min(top + patch_size, height) - 1),
            fill=255,
        )
    return mask


def _ground_truth_mask(
    example: dict[str, Any], image_size: tuple[int, int], patch_size: int
) -> Image.Image:
    """Build a display-only patch mask from recorded ground-truth-positive patches."""
    width, height = image_size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    for patch in example.get("patches", []):
        if not patch.get("ground_truth_positive", False):
            continue
        row = int(patch["row"])
        column = int(patch["column"])
        left = column * patch_size
        top = row * patch_size
        draw.rectangle(
            (left, top, min(left + patch_size, width) - 1, min(top + patch_size, height) - 1),
            fill=255,
        )
    return mask


def _find_sample_images(
    dataset_root: Path, split: str, sample_id: str
) -> tuple[Path, Path, Path] | None:
    """Locate the Phase 3/5 before, after, and label images for one sample."""
    base = dataset_root / "images" / split
    paths = tuple(base / part / f"{sample_id}.png" for part in ("A", "B", "label"))
    return paths if all(path.is_file() for path in paths) else None


def _metric_cards(metrics: dict[str, Any]) -> None:
    """Render the Phase 2 model metrics."""
    columns = st.columns(4)
    values = (
        ("Accuracy", metrics.get("accuracy")),
        ("Precision", metrics.get("macro_precision")),
        ("Recall", metrics.get("macro_recall")),
        ("F1", metrics.get("macro_f1")),
    )
    for column, (label, value) in zip(columns, values, strict=True):
        column.metric(label, "—" if value is None else f"{float(value):.4f}")


def _show_confusion_matrix(metrics: dict[str, Any]) -> None:
    """Render the generated Phase 2 confusion matrix as a table."""
    matrix = metrics.get("confusion_matrix")
    if not isinstance(matrix, list):
        st.info("No generated confusion matrix was found in the EuroSAT metrics artifact.")
        return
    st.dataframe(matrix, use_container_width=True, hide_index=True)


def _show_detection_example(
    example: dict[str, Any],
    *,
    dataset_root: Path,
    split: str,
    patch_size: int,
) -> None:
    """Render the selected Phase 5 example without running new inference."""
    sample_id = str(example.get("sample_id", ""))
    paths = _find_sample_images(dataset_root, split, sample_id)
    if paths is None:
        st.warning(
            "The Phase 5 JSON is available, but the source Forest-Change images are not "
            "available at the configured dataset root."
        )
        st.json(
            {
                "sample_id": sample_id,
                "patch_count": example.get("patch_count"),
                "candidate_count": example.get("candidate_count"),
                "confusion_matrix": example.get("confusion_matrix"),
            }
        )
        return

    before_path, after_path, label_path = paths
    with Image.open(before_path) as before_file, Image.open(after_path) as after_file:
        before = before_file.convert("RGB")
        after = after_file.convert("RGB")

    predicted = _prediction_mask(example, before.size, patch_size)
    ground_truth = _ground_truth_mask(example, before.size, patch_size)

    columns = st.columns(4)
    columns[0].image(before, caption="Before", use_container_width=True)
    columns[1].image(after, caption="After", use_container_width=True)
    columns[2].image(ground_truth, caption="Ground truth", use_container_width=True)
    columns[3].image(predicted, caption="Prediction", use_container_width=True)

    st.caption(
        f"Sample {sample_id}: {example.get('patch_count', 0)} patches, "
        f"{example.get('candidate_count', 0)} candidates."
    )

    st.subheader("Detection metrics")
    detection_columns = st.columns(3)
    detection_columns[0].metric("Precision", f"{float(example.get('precision', 0.0)):.4f}")
    detection_columns[1].metric("Recall", f"{float(example.get('recall', 0.0)):.4f}")
    detection_columns[2].metric("F1", f"{float(example.get('f1', 0.0)):.4f}")

    with Image.open(label_path) as label_file:
        st.caption("Original benchmark change mask")
        st.image(label_file.convert("L"), use_container_width=True)


def _show_alerts(phase5: dict[str, Any]) -> None:
    """Render generated alert events and their recorded delivery results."""
    events = phase5.get("candidate_events", [])
    if not events:
        st.info("No candidate alert events were generated by the Phase 5 artifact.")
        return

    for index, record in enumerate(events, start=1):
        event = record.get("event", {})
        with st.expander(
            f"{index}. {event.get('event_id', 'unknown event')} "
            f"— {event.get('priority', 'unknown priority')}"
        ):
            details = {
                "event_id": event.get("event_id"),
                "confidence": event.get("confidence"),
                "priority": event.get("priority"),
                "tile": {
                    "row": event.get("patch_row"),
                    "column": event.get("patch_column"),
                },
                "location": event.get("location"),
                "detected_at": event.get("detected_at"),
            }
            st.json(details)

            notifications = record.get("notifications", [])
            st.write("Delivery status")
            if not notifications:
                st.warning("No recipient delivery records were recorded.")
                continue

            rows = []
            for notification in notifications:
                rows.append(
                    {
                        "recipient": notification.get("recipient"),
                        "status": "delivered",
                        "route": " → ".join(notification.get("path", [])),
                        "route_cost": notification.get("path_cost"),
                        "delivered_at": notification.get("delivered_at"),
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.metric(
                "Notification latency (ms)",
                f"{float(record.get('notification_latency_ms', 0.0)):.3f}",
            )


def main() -> None:
    """Render the Phase 6 ForestWatch dashboard."""
    st.set_page_config(page_title="ForestWatch", layout="wide")
    st.title("ForestWatch")
    st.caption("Phase 6 — research artifact dashboard")

    with st.sidebar:
        st.header("Artifacts")
        metrics_path = Path(
            st.text_input("EuroSAT metrics", str(DEFAULT_METRICS))
        ).expanduser()
        phase5_path = Path(
            st.text_input("Phase 5 results", str(DEFAULT_PHASE5))
        ).expanduser()
        dataset_root = Path(
            st.text_input("Forest-Change dataset", str(DEFAULT_DATASET))
        ).expanduser()
        split = st.text_input("Dataset split", "test")
        patch_size = st.number_input("Patch size (pixels)", min_value=1, value=64, step=1)

    metrics = _load_json(metrics_path)
    phase5 = _load_json(phase5_path)

    if metrics is None:
        st.warning(f"EuroSAT metrics artifact not found: {metrics_path}")
    else:
        st.header("Model performance")
        _metric_cards(metrics)
        st.subheader("EuroSAT confusion matrix")
        _show_confusion_matrix(metrics)

    if phase5 is None:
        st.warning(f"Phase 5 artifact not found: {phase5_path}")
        return

    st.header("Forest-change detection")
    examples = phase5.get("detection_summary", {})
    st.write(
        f"Examples: {examples.get('example_count', 0)} · "
        f"Patches: {examples.get('patch_count', 0)} · "
        f"Candidates: {examples.get('candidate_count', 0)}"
    )

    example_list = phase5.get("examples", [])
    if isinstance(example_list, list) and example_list:
        sample_ids = [str(example.get("sample_id", "unknown")) for example in example_list]
        selected_id = st.selectbox("Sample", sample_ids)
        selected = next(
            example for example in example_list if str(example.get("sample_id")) == selected_id
        )
        _show_detection_example(
            selected,
            dataset_root=dataset_root,
            split=split,
            patch_size=int(patch_size),
        )
    else:
        st.info("No per-example detection records are present in the Phase 5 artifact.")

    st.header("Priority alerts and network delivery")
    _show_alerts(phase5)


if __name__ == "__main__":
    main()
