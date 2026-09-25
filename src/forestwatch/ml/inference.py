from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torch import nn

from forestwatch.ml.constants import EUROSAT_CHECKPOINT_CLASSES
from forestwatch.ml.data import build_checkpoint_eval_transform, load_rgb_image


@dataclass(frozen=True)
class Prediction:
    class_index: int
    class_name: str
    confidence: float


def predict_tensor(
    model: nn.Module,
    tensor: torch.Tensor,
    *,
    device: torch.device,
    class_names: tuple[str, ...] = EUROSAT_CHECKPOINT_CLASSES,
) -> list[Prediction]:
    """Predict a batch of normalized RGB tensors."""
    model.eval()
    with torch.inference_mode():
        logits = model(tensor.to(device, non_blocking=device.type == "cuda"))
        probabilities = torch.softmax(logits, dim=1)
        confidences, indices = probabilities.max(dim=1)

    return [
        Prediction(
            class_index=int(index),
            class_name=class_names[int(index)],
            confidence=float(confidence),
        )
        for index, confidence in zip(indices.cpu(), confidences.cpu(), strict=True)
    ]


def predict_image(
    model: nn.Module,
    image_path: Path,
    *,
    device: torch.device,
    class_names: tuple[str, ...] = EUROSAT_CHECKPOINT_CLASSES,
) -> Prediction:
    """Predict one EuroSAT RGB image with checkpoint-compatible preprocessing."""
    image = load_rgb_image(image_path)
    tensor = build_checkpoint_eval_transform()(image).unsqueeze(0)
    return predict_tensor(model, tensor, device=device, class_names=class_names)[0]


def predict_pil_image(
    model: nn.Module,
    image: Image.Image,
    *,
    device: torch.device,
    class_names: tuple[str, ...] = EUROSAT_CHECKPOINT_CLASSES,
) -> Prediction:
    """Predict one in-memory RGB image with checkpoint-compatible preprocessing."""
    rgb_image = image.convert("RGB")
    tensor = build_checkpoint_eval_transform()(rgb_image).unsqueeze(0)
    return predict_tensor(model, tensor, device=device, class_names=class_names)[0]
