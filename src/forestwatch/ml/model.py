from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file, save_file
from torch import nn
from torchvision.models import ResNet50_Weights, resnet50

from forestwatch.ml.constants import (
    EUROSAT_CLASSES,
    EUROSAT_HF_MODEL_FILENAME,
    EUROSAT_HF_MODEL_ID,
    EUROSAT_HF_MODEL_REVISION,
)


def build_resnet50(
    *,
    num_classes: int = len(EUROSAT_CLASSES),
    imagenet_pretrained: bool = False,
    freeze_backbone: bool = False,
) -> nn.Module:
    """Create a torchvision ResNet50 with the required EuroSAT classifier head."""
    weights = ResNet50_Weights.DEFAULT if imagenet_pretrained else None
    model = resnet50(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, num_classes)

    if freeze_backbone:
        for parameter in model.parameters():
            parameter.requires_grad = False
        for parameter in model.fc.parameters():
            parameter.requires_grad = True

    return model


def _candidate_state_dicts(state_dict: dict[str, torch.Tensor]) -> list[dict[str, torch.Tensor]]:
    candidates = [state_dict]
    prefixes = ("module.", "model.", "backbone.")
    for prefix in prefixes:
        candidates.append(
            {
                (key[len(prefix) :] if key.startswith(prefix) else key): value
                for key, value in state_dict.items()
            }
        )

    for candidate in list(candidates):
        if "classifier.weight" in candidate and "fc.weight" not in candidate:
            remapped = dict(candidate)
            remapped["fc.weight"] = remapped.pop("classifier.weight")
            if "classifier.bias" in remapped:
                remapped["fc.bias"] = remapped.pop("classifier.bias")
            candidates.append(remapped)
    return candidates


def _load_state_dict(model: nn.Module, state_dict: dict[str, torch.Tensor]) -> None:
    model_keys = set(model.state_dict())
    best = max(
        _candidate_state_dicts(state_dict),
        key=lambda item: len(model_keys.intersection(item)),
    )
    missing, unexpected = model.load_state_dict(best, strict=False)

    allowed_missing = {key for key in missing if key.endswith("num_batches_tracked")}
    real_missing = [key for key in missing if key not in allowed_missing]
    if real_missing or unexpected:
        raise RuntimeError(
            "Checkpoint is incompatible with torchvision ResNet50. "
            f"Missing keys: {real_missing[:8]}; unexpected keys: {unexpected[:8]}"
        )


def load_local_safetensors(model: nn.Module, checkpoint_path: Path) -> nn.Module:
    """Load a safetensors checkpoint into a ResNet50-compatible model."""
    state_dict = load_file(str(checkpoint_path), device="cpu")
    _load_state_dict(model, state_dict)
    return model


def load_eurosat_checkpoint(
    model: nn.Module,
    *,
    model_id: str = EUROSAT_HF_MODEL_ID,
    filename: str = EUROSAT_HF_MODEL_FILENAME,
    revision: str = EUROSAT_HF_MODEL_REVISION,
    cache_dir: Path | None = None,
) -> nn.Module:
    """Download the public MIT-licensed EuroSAT ResNet50 weights and load them."""
    kwargs: dict[str, Any] = {
        "repo_id": model_id,
        "filename": filename,
        "revision": revision,
    }
    if cache_dir is not None:
        kwargs["cache_dir"] = str(cache_dir.expanduser().resolve())
    checkpoint_path = Path(hf_hub_download(**kwargs))
    return load_local_safetensors(model, checkpoint_path)


def save_safetensors(model: nn.Module, path: Path) -> None:
    """Save only model weights in the portable safetensors format."""
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    state_dict = {
        key: value.detach().cpu().contiguous() for key, value in model.state_dict().items()
    }
    save_file(state_dict, str(path))
