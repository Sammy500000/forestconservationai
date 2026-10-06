from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import torch
from PIL import Image

from forestwatch.detection.data import discover_examples
from forestwatch.detection.pipeline import analyze_example
from forestwatch.ml.constants import EUROSAT_CHECKPOINT_CLASSES
from forestwatch.networking.integration import deliver_in_memory_concurrently
from forestwatch.networking.router import PriorityRouter
from forestwatch.networking.topology import build_default_topology
from forestwatch.schemas.events import AlertPriority, EventType, ForestEvent


class _FixedModel(torch.nn.Module):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        indices = inputs[:, 0, 0, 0].round().long()
        logits = torch.full((inputs.size(0), 10), -10.0)
        logits.scatter_(1, indices.unsqueeze(1), 10.0)
        return logits


class _MarkerTransform:
    def __call__(self, image: Image.Image) -> torch.Tensor:
        marker = int(image.getpixel((0, 0))[0])
        tensor = torch.zeros((3, 224, 224), dtype=torch.float32)
        tensor[0, 0, 0] = marker
        return tensor


def test_detection_pipeline_uses_before_after_predictions_and_mask(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "forest_change"
    for part in ("A", "B", "label"):
        (root / "images" / "test" / part).mkdir(parents=True)

    before = Image.new("RGB", (128, 64), (0, 0, 0))
    after = Image.new("RGB", (128, 64), (0, 0, 0))
    after.putpixel((0, 0), (3, 0, 0))
    mask = Image.new("L", (128, 64), 0)
    mask.paste(255, (0, 0, 64, 64))

    before_path = root / "images" / "test" / "A" / "sample.png"
    after_path = root / "images" / "test" / "B" / "sample.png"
    mask_path = root / "images" / "test" / "label" / "sample.png"
    before.save(before_path)
    after.save(after_path)
    mask.save(mask_path)

    from forestwatch.ml import data as ml_data

    monkeypatch.setattr(ml_data, "build_checkpoint_eval_transform", lambda: _MarkerTransform())
    result = analyze_example(
        _FixedModel(),
        discover_examples(root)[0],
        device=torch.device("cpu"),
    )

    assert result["candidate_count"] == 1
    assert result["confusion_matrix"] == {"tn": 1, "fp": 0, "fn": 0, "tp": 1}
    assert result["f1"] == pytest.approx(1.0)


def test_event_from_candidate_has_required_metadata() -> None:
    event = ForestEvent(
        event_id="EVT-1",
        event_type=EventType.FOREST_LOSS_CANDIDATE,
        priority=AlertPriority.CRITICAL,
        confidence=0.93,
        location={"latitude": 21.0, "longitude": 86.0},
        detected_at=datetime.now(UTC),
        before_class="Forest",
        after_class="AnnualCrop",
        sample_id="sample",
        patch_row=2,
        patch_column=3,
    )
    assert event.before_class == "Forest"
    assert event.after_class == "AnnualCrop"
    assert event.sample_id == "sample"
    assert event.patch_row == 2
    assert event.patch_column == 3


def test_concurrent_in_memory_delivery() -> None:
    router = PriorityRouter(build_default_topology())
    event = ForestEvent(
        event_id="EVT-2",
        event_type=EventType.FOREST_LOSS_CANDIDATE,
        priority=AlertPriority.CRITICAL,
        confidence=0.95,
        location={"latitude": 0.0, "longitude": 0.0},
        detected_at=datetime.now(UTC),
    )
    results = deliver_in_memory_concurrently(
        event,
        recipients=("node_a", "district", "control_room"),
        router=router,
    )
    assert {result.recipient for result in results} == {
        "node_a",
        "district",
        "control_room",
    }
    assert all(result.event_id == event.event_id for result in results)
    assert all(result.path[0] == "forest_hub" for result in results)
    assert all(result.delivered_at.tzinfo is not None for result in results)
