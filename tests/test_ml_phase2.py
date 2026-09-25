from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import torch
from PIL import Image

pytest.importorskip("torch")
pytest.importorskip("torchvision")
pytest.importorskip("safetensors")
pytest.importorskip("huggingface_hub")

from safetensors.torch import save_file

from forestwatch.ml.constants import EUROSAT_CHECKPOINT_CLASSES, EUROSAT_CLASSES
from forestwatch.ml.data import (
    build_checkpoint_eval_transform,
    build_eval_transform,
    split_indices,
)
from forestwatch.ml.model import build_resnet50, load_local_safetensors


def test_eurosat_classes_match_reference() -> None:
    assert EUROSAT_CLASSES == (
        "AnnualCrop",
        "Forest",
        "HerbaceousVegetation",
        "Highway",
        "Industrial",
        "Pasture",
        "PermanentCrop",
        "Residential",
        "River",
        "SeaLake",
    )


def test_split_is_deterministic_and_matches_reference_sizes() -> None:
    first = split_indices(27_000, seed=42)
    second = split_indices(27_000, seed=42)
    assert first == second
    assert tuple(map(len, first)) == (21_600, 2_700, 2_700)
    assert len(set().union(*[set(part) for part in first])) == 27_000


def test_evaluation_transform_matches_resnet50_input_contract() -> None:
    image = Image.new("RGB", (64, 64))
    transformed = build_eval_transform()(image)
    assert transformed.shape == (3, 224, 224)
    assert transformed.dtype == torch.float32


def test_resnet50_has_ten_output_classes() -> None:
    model = build_resnet50()
    assert model.fc.out_features == 10


def test_local_safetensors_round_trip() -> None:
    model = build_resnet50()
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "model.safetensors"
        save_file(
            {key: value.detach().cpu().contiguous() for key, value in model.state_dict().items()},
            str(path),
        )
        loaded = build_resnet50()
        load_local_safetensors(loaded, path)

    original = model.state_dict()
    restored = loaded.state_dict()
    assert original.keys() == restored.keys()
    for key in original:
        assert torch.equal(original[key], restored[key])


def test_checkpoint_label_order_is_mapped_explicitly() -> None:
    assert set(EUROSAT_CHECKPOINT_CLASSES) == set(EUROSAT_CLASSES)
    assert EUROSAT_CHECKPOINT_CLASSES.index("Forest") == 0
    assert EUROSAT_CLASSES.index("Forest") == 1


def test_checkpoint_transform_matches_224_input_contract() -> None:
    image = Image.new("RGB", (64, 64))
    transformed = build_checkpoint_eval_transform()(image)
    assert transformed.shape == (3, 224, 224)


class _FixedLogitModel(torch.nn.Module):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        indices = inputs[:, 0, 0, 0].long()
        logits = torch.full((inputs.size(0), 10), -10.0)
        logits.scatter_(1, indices.unsqueeze(1), 10.0)
        return logits


def test_evaluator_maps_checkpoint_logit_order_to_folder_order() -> None:
    from torch.utils.data import DataLoader, TensorDataset

    from forestwatch.ml.evaluate import evaluate_model

    # Checkpoint indices: Forest=0, AnnualCrop=3, SeaLake=4.
    inputs = torch.zeros((3, 3, 224, 224))
    inputs[:, 0, 0, 0] = torch.tensor([0, 3, 4])
    labels = torch.tensor([1, 0, 9])  # Folder order: Forest, AnnualCrop, SeaLake.
    loader = DataLoader(TensorDataset(inputs, labels), batch_size=3)

    result = evaluate_model(
        _FixedLogitModel(),
        loader,
        device=torch.device("cpu"),
        model_class_names=EUROSAT_CHECKPOINT_CLASSES,
    )
    assert result.accuracy == 1.0
    assert result.sample_count == 3
