from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import classification_report, confusion_matrix
from torch import nn
from torch.utils.data import DataLoader

from forestwatch.ml.constants import EUROSAT_CLASSES


@dataclass(frozen=True)
class EvaluationResult:
    loss: float
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    sample_count: int
    report: dict[str, Any]
    confusion: list[list[int]]


def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader[object],
    *,
    device: torch.device,
    model_class_names: tuple[str, ...] = EUROSAT_CLASSES,
) -> EvaluationResult:
    """Evaluate classification performance and collect standard research metrics."""
    criterion = nn.CrossEntropyLoss()
    model.eval()

    total_loss = 0.0
    total_samples = 0
    all_labels: list[int] = []
    all_predictions: list[int] = []

    dataset_index_by_name = {name: index for index, name in enumerate(EUROSAT_CLASSES)}
    model_index_by_name = {name: index for index, name in enumerate(model_class_names)}
    if set(model_class_names) != set(EUROSAT_CLASSES):
        raise ValueError("model_class_names must contain the same ten EuroSAT classes")

    dataset_to_model = torch.tensor(
        [model_index_by_name[name] for name in EUROSAT_CLASSES],
        dtype=torch.long,
        device=device,
    )
    model_to_dataset = torch.tensor(
        [dataset_index_by_name[name] for name in model_class_names],
        dtype=torch.long,
        device=device,
    )

    with torch.inference_mode():
        for images, labels in dataloader:
            images = images.to(device, non_blocking=device.type == "cuda")
            labels = labels.to(device, non_blocking=device.type == "cuda")
            model_labels = dataset_to_model[labels]
            logits = model(images)
            loss = criterion(logits, model_labels)
            model_predictions = logits.argmax(dim=1)
            predictions = model_to_dataset[model_predictions]

            batch_size = labels.size(0)
            total_loss += float(loss.item()) * batch_size
            total_samples += batch_size
            all_labels.extend(labels.cpu().tolist())
            all_predictions.extend(predictions.cpu().tolist())

    if total_samples == 0:
        raise ValueError("Evaluation dataloader is empty")

    report = classification_report(
        all_labels,
        all_predictions,
        labels=list(range(len(EUROSAT_CLASSES))),
        target_names=list(EUROSAT_CLASSES),
        output_dict=True,
        zero_division=0,
    )
    confusion = confusion_matrix(
        all_labels,
        all_predictions,
        labels=list(range(len(EUROSAT_CLASSES))),
    ).tolist()

    return EvaluationResult(
        loss=total_loss / total_samples,
        accuracy=float(report["accuracy"]),
        macro_precision=float(report["macro avg"]["precision"]),
        macro_recall=float(report["macro avg"]["recall"]),
        macro_f1=float(report["macro avg"]["f1-score"]),
        sample_count=total_samples,
        report=report,
        confusion=confusion,
    )


def save_metrics(result: EvaluationResult, path: Path) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "loss": result.loss,
        "accuracy": result.accuracy,
        "macro_precision": result.macro_precision,
        "macro_recall": result.macro_recall,
        "macro_f1": result.macro_f1,
        "sample_count": result.sample_count,
        "report": result.report,
        "confusion_matrix": result.confusion,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_classification_report(result: EvaluationResult, path: Path) -> None:
    """Save the per-class report as CSV for easy inclusion in a report."""
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for class_name in EUROSAT_CLASSES:
        metrics = result.report[class_name]
        rows.append(
            {
                "class": class_name,
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1-score"],
                "support": int(metrics["support"]),
            }
        )

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_confusion_matrix(result: EvaluationResult, path: Path) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    matrix = np.asarray(result.confusion)
    figure, axis = plt.subplots(figsize=(10, 8))
    image = axis.imshow(matrix, interpolation="nearest")
    figure.colorbar(image, ax=axis)
    axis.set(
        xticks=np.arange(len(EUROSAT_CLASSES)),
        yticks=np.arange(len(EUROSAT_CLASSES)),
        xticklabels=EUROSAT_CLASSES,
        yticklabels=EUROSAT_CLASSES,
        xlabel="Predicted",
        ylabel="Actual",
        title="EuroSAT ResNet50 Confusion Matrix",
    )
    axis.tick_params(axis="x", rotation=45)

    threshold = matrix.max() / 2 if matrix.size else 0
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            axis.text(
                column_index,
                row_index,
                int(matrix[row_index, column_index]),
                ha="center",
                va="center",
                color="white" if matrix[row_index, column_index] > threshold else "black",
            )

    figure.tight_layout()
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
