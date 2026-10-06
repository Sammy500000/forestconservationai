"""End-to-end forest-change inference and evaluation helpers."""
from __future__ import annotations

import json
from pathlib import Path

import torch
from PIL import Image
from torch import nn

from forestwatch.detection.change_detection import ChangePrediction, build_candidate_change
from forestwatch.detection.data import ForestChangeExample, discover_examples
from forestwatch.detection.patching import change_fraction, iter_aligned_patches
from forestwatch.ml.constants import EUROSAT_CHECKPOINT_CLASSES
from forestwatch.ml.inference import Prediction, predict_tensor


def _predict_patches(
    model: nn.Module,
    patches: list[Image.Image],
    *,
    device: torch.device,
    batch_size: int = 32,
) -> list[Prediction]:
    """Predict all patches in batches using the public checkpoint preprocessing."""
    if not patches:
        return []

    from forestwatch.ml.data import build_checkpoint_eval_transform

    transform = build_checkpoint_eval_transform()
    tensors = torch.stack([transform(image) for image in patches])
    predictions: list[Prediction] = []
    for start in range(0, len(tensors), batch_size):
        predictions.extend(
            predict_tensor(
                model,
                tensors[start : start + batch_size],
                device=device,
                class_names=EUROSAT_CHECKPOINT_CLASSES,
            )
        )
    return predictions


def analyze_example(
    model: nn.Module,
    example: ForestChangeExample,
    *,
    device: torch.device,
    patch_size: int = 64,
    confidence_threshold: float = 0.70,
    ground_truth_threshold: float = 0.10,
) -> dict[str, object]:
    """Run two-date patch classification and compare candidates to the reference mask."""
    before, after, mask = example.load()
    patches = iter_aligned_patches(before, after, mask, patch_size=patch_size)

    before_predictions = _predict_patches(
        model,
        [patch.before for patch in patches],
        device=device,
    )
    after_predictions = _predict_patches(
        model,
        [patch.after for patch in patches],
        device=device,
    )

    candidates: list[dict[str, object]] = []
    patch_records: list[dict[str, object]] = []

    for patch, before_pred, after_pred in zip(
        patches,
        before_predictions,
        after_predictions,
        strict=True,
    ):
        prediction = ChangePrediction(
            before_class=before_pred.class_name,
            before_confidence=before_pred.confidence,
            after_class=after_pred.class_name,
            after_confidence=after_pred.confidence,
        )
        candidate = build_candidate_change(
            prediction,
            row=patch.row,
            column=patch.column,
            confidence_threshold=confidence_threshold,
        )
        truth_fraction = change_fraction(patch.mask)
        truth_positive = truth_fraction >= ground_truth_threshold

        record = {
            "row": patch.row,
            "column": patch.column,
            "before_class": before_pred.class_name,
            "before_confidence": before_pred.confidence,
            "after_class": after_pred.class_name,
            "after_confidence": after_pred.confidence,
            "candidate": candidate is not None,
            "ground_truth_fraction": truth_fraction,
            "ground_truth_positive": truth_positive,
        }
        patch_records.append(record)

        if candidate is not None:
            candidates.append(
                {
                    "row": candidate.row,
                    "column": candidate.column,
                    "before_class": candidate.before_class,
                    "after_class": candidate.after_class,
                    "confidence": candidate.confidence,
                    "ground_truth_fraction": truth_fraction,
                    "ground_truth_positive": truth_positive,
                }
            )

    predicted = [bool(record["candidate"]) for record in patch_records]
    truth = [bool(record["ground_truth_positive"]) for record in patch_records]
    tp = sum(pred and actual for pred, actual in zip(predicted, truth, strict=True))
    fp = sum(pred and not actual for pred, actual in zip(predicted, truth, strict=True))
    fn = sum(not pred and actual for pred, actual in zip(predicted, truth, strict=True))
    tn = sum(not pred and not actual for pred, actual in zip(predicted, truth, strict=True))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "sample_id": example.sample_id,
        "split": example.split,
        "image_size": list(before.size),
        "patch_count": len(patches),
        "candidate_count": len(candidates),
        "ground_truth_positive_count": sum(truth),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "candidates": candidates,
        "patches": patch_records,
    }


def run_detection(
    model: nn.Module,
    dataset_root: Path,
    *,
    split: str = "test",
    device: torch.device,
    patch_size: int = 64,
    confidence_threshold: float = 0.70,
    ground_truth_threshold: float = 0.10,
    limit: int | None = None,
) -> dict[str, object]:
    """Run detection across a dataset split and aggregate patch-level metrics."""
    examples = discover_examples(dataset_root, split=split)
    if limit is not None:
        if limit <= 0:
            raise ValueError("limit must be positive when provided")
        examples = examples[:limit]
    if not examples:
        raise RuntimeError(f"No Forest-Change examples found for split={split!r}.")

    results = [
        analyze_example(
            model,
            example,
            device=device,
            patch_size=patch_size,
            confidence_threshold=confidence_threshold,
            ground_truth_threshold=ground_truth_threshold,
        )
        for example in examples
    ]

    total = {"tn": 0, "fp": 0, "fn": 0, "tp": 0}
    for result in results:
        matrix = result["confusion_matrix"]
        for key in total:
            total[key] += int(matrix[key])

    tp = total["tp"]
    fp = total["fp"]
    fn = total["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "split": split,
        "example_count": len(results),
        "patch_count": sum(int(result["patch_count"]) for result in results),
        "candidate_count": sum(int(result["candidate_count"]) for result in results),
        "confusion_matrix": total,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "examples": results,
    }


def save_detection_result(result: dict[str, object], output_path: Path) -> None:
    """Write detection output as JSON."""
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
