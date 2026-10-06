from __future__ import annotations

from PIL import Image
import pytest

from forestwatch.detection.change_detection import (
    ChangePrediction,
    build_candidate_change,
    is_forest_loss_candidate,
)
from forestwatch.detection.data import ForestChangeExample
from forestwatch.detection.patching import change_fraction, expected_patch_count, iter_aligned_patches


def test_aligned_patching_produces_corresponding_grid() -> None:
    before = Image.new("RGB", (128, 128))
    after = Image.new("RGB", (128, 128))
    mask = Image.new("L", (128, 128))
    patches = iter_aligned_patches(before, after, mask, patch_size=64)
    assert len(patches) == 4
    assert {(p.row, p.column) for p in patches} == {(0, 0), (0, 1), (1, 0), (1, 1)}
    assert all(p.before.size == (64, 64) for p in patches)
    assert expected_patch_count(128, 128, 64) == 4


def test_change_fraction_counts_binary_mask() -> None:
    mask = Image.new("L", (4, 4), 0)
    mask.putpixel((0, 0), 255)
    mask.putpixel((1, 0), 255)
    assert change_fraction(mask) == pytest.approx(2 / 16)


def test_forest_loss_rule_requires_both_confidences() -> None:
    positive = ChangePrediction("Forest", 0.90, "AnnualCrop", 0.80)
    negative = ChangePrediction("Forest", 0.60, "AnnualCrop", 0.95)
    assert is_forest_loss_candidate(positive)
    assert not is_forest_loss_candidate(negative)


def test_candidate_record_uses_lower_confidence() -> None:
    prediction = ChangePrediction("Forest", 0.91, "Residential", 0.83)
    candidate = build_candidate_change(prediction, row=2, column=3)
    assert candidate is not None
    assert candidate.confidence == pytest.approx(0.83)
    assert (candidate.row, candidate.column) == (2, 3)


def test_forest_change_example_loads_independent_images(tmp_path) -> None:
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    mask = tmp_path / "mask.png"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(before)
    Image.new("RGB", (8, 8), (4, 5, 6)).save(after)
    Image.new("L", (8, 8), 255).save(mask)
    example = ForestChangeExample(before, after, mask, "sample-1", "test")
    before_image, after_image, mask_image = example.load()
    assert before_image.mode == "RGB"
    assert after_image.mode == "RGB"
    assert mask_image.mode == "L"
