from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from forestwatch.dashboard.app import _ground_truth_mask, _load_json, _prediction_mask


def test_load_json_reads_generated_artifact(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps({"accuracy": 0.91}), encoding="utf-8")

    assert _load_json(path) == {"accuracy": 0.91}


def test_load_json_returns_none_for_missing_artifact(tmp_path: Path) -> None:
    assert _load_json(tmp_path / "missing.json") is None


def test_dashboard_masks_use_recorded_patch_flags() -> None:
    example = {
        "patches": [
            {"row": 0, "column": 0, "candidate": True, "ground_truth_positive": True},
            {"row": 0, "column": 1, "candidate": False, "ground_truth_positive": True},
        ]
    }

    prediction = _prediction_mask(example, (128, 64), 64)
    truth = _ground_truth_mask(example, (128, 64), 64)

    assert prediction.getpixel((10, 10)) == 255
    assert prediction.getpixel((70, 10)) == 0
    assert truth.getpixel((10, 10)) == 255
    assert truth.getpixel((70, 10)) == 255


def test_dashboard_mask_dimensions_match_source_image() -> None:
    example = {"patches": [{"row": 1, "column": 1, "candidate": True}]}
    mask = _prediction_mask(example, (100, 90), 64)

    assert isinstance(mask, Image.Image)
    assert mask.size == (100, 90)
