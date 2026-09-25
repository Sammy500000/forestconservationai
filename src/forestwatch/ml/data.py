from __future__ import annotations

import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import transforms
from torchvision.datasets import ImageFolder

from forestwatch.ml.constants import (
    CHECKPOINT_MEAN,
    CHECKPOINT_STD,
    EUROSAT_CLASSES,
    EUROSAT_ZIP_MD5,
    EUROSAT_ZIP_URL,
    IMAGENET_MEAN,
    IMAGENET_STD,
)


@dataclass(frozen=True)
class EuroSATDatasetSummary:
    root: Path
    classes: tuple[str, ...]
    class_counts: dict[str, int]
    total_images: int


@dataclass(frozen=True)
class EuroSATSplits:
    train: Dataset[object]
    validation: Dataset[object]
    test: Dataset[object]
    classes: tuple[str, ...]


def build_train_transform(input_size: int = 224) -> transforms.Compose:
    """Build the training transform described by the project reference."""
    return transforms.Compose(
        [
            transforms.Resize((input_size, input_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def build_checkpoint_eval_transform() -> transforms.Compose:
    """Build the preprocessing used by the public EuroSAT ResNet50 checkpoint."""
    return transforms.Compose(
        [
            transforms.Resize(232, interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=CHECKPOINT_MEAN, std=CHECKPOINT_STD),
        ]
    )


def build_eval_transform(input_size: int = 224) -> transforms.Compose:
    """Build a deterministic ImageNet-normalized evaluation transform."""
    return transforms.Compose(
        [
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def _is_dataset_root(path: Path) -> bool:
    return path.is_dir() and all((path / class_name).is_dir() for class_name in EUROSAT_CLASSES)


def find_eurosat_root(root: Path) -> Path:
    """Find the directory containing all ten EuroSAT class directories."""
    root = root.expanduser().resolve()
    if _is_dataset_root(root):
        return root

    for candidate in (path for path in root.rglob("*") if path.is_dir()):
        if _is_dataset_root(candidate):
            return candidate

    raise FileNotFoundError(
        f"Could not find a EuroSAT RGB directory below {root}. "
        "Expected ten class directories such as Forest and AnnualCrop."
    )


def summarize_eurosat(root: Path) -> EuroSATDatasetSummary:
    """Validate and summarize an extracted EuroSAT RGB dataset."""
    dataset_root = find_eurosat_root(root)
    class_counts = {
        class_name: sum(1 for path in (dataset_root / class_name).iterdir() if path.is_file())
        for class_name in EUROSAT_CLASSES
    }
    total_images = sum(class_counts.values())
    return EuroSATDatasetSummary(
        root=dataset_root,
        classes=EUROSAT_CLASSES,
        class_counts=class_counts,
        total_images=total_images,
    )


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract(zip_file: zipfile.ZipFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in zip_file.infolist():
        target = (destination / member.filename).resolve()
        if target != destination and destination not in target.parents:
            raise ValueError(f"Unsafe path in dataset archive: {member.filename}")
    zip_file.extractall(destination)


def download_eurosat(destination: Path, *, force: bool = False) -> EuroSATDatasetSummary:
    """Download and extract the official EuroSAT RGB archive from Zenodo."""
    destination = destination.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    if not force:
        try:
            return summarize_eurosat(destination)
        except FileNotFoundError:
            pass

    with tempfile.TemporaryDirectory(prefix="eurosat-download-") as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "EuroSAT_RGB.zip"
        urllib.request.urlretrieve(EUROSAT_ZIP_URL, zip_path)

        observed_md5 = _md5(zip_path)
        if observed_md5 != EUROSAT_ZIP_MD5:
            raise RuntimeError(
                "EuroSAT archive checksum mismatch: "
                f"expected {EUROSAT_ZIP_MD5}, got {observed_md5}"
            )

        extract_root = temp_path / "extracted"
        extract_root.mkdir()
        with zipfile.ZipFile(zip_path) as archive:
            _safe_extract(archive, extract_root)

        dataset_root = find_eurosat_root(extract_root)
        target_root = destination / "EuroSAT_RGB"
        if target_root.exists():
            if not force:
                return summarize_eurosat(destination)
            shutil.rmtree(target_root)
        shutil.copytree(dataset_root, target_root)

    return summarize_eurosat(destination)


def split_indices(
    dataset_size: int,
    *,
    validation_fraction: float = 0.10,
    test_fraction: float = 0.10,
    seed: int = 42,
) -> tuple[list[int], list[int], list[int]]:
    """Create deterministic 80/10/10-style random splits."""
    if dataset_size < 3:
        raise ValueError("dataset_size must be at least 3")
    if not 0 <= validation_fraction < 1:
        raise ValueError("validation_fraction must be in [0, 1)")
    if not 0 <= test_fraction < 1:
        raise ValueError("test_fraction must be in [0, 1)")
    if validation_fraction + test_fraction >= 1:
        raise ValueError("validation_fraction + test_fraction must be less than 1")

    generator = torch.Generator().manual_seed(seed)
    indices = torch.randperm(dataset_size, generator=generator).tolist()

    test_size = int(dataset_size * test_fraction)
    validation_size = int(dataset_size * validation_fraction)
    test_indices = indices[:test_size]
    validation_indices = indices[test_size : test_size + validation_size]
    train_indices = indices[test_size + validation_size :]
    return train_indices, validation_indices, test_indices


def build_eurosat_splits(
    root: Path,
    *,
    input_size: int = 224,
    validation_fraction: float = 0.10,
    test_fraction: float = 0.10,
    seed: int = 42,
    eval_transform: Callable[[Image.Image], torch.Tensor] | None = None,
) -> EuroSATSplits:
    """Build train/validation/test subsets with separate augmentation policies."""
    dataset_root = find_eurosat_root(root)
    train_base = ImageFolder(dataset_root, transform=build_train_transform(input_size))
    evaluation_transform = (
        eval_transform if eval_transform is not None else build_eval_transform(input_size)
    )
    eval_base = ImageFolder(dataset_root, transform=evaluation_transform)

    expected = list(EUROSAT_CLASSES)
    if train_base.classes != expected or eval_base.classes != expected:
        raise ValueError(
            f"Unexpected EuroSAT class ordering. Expected {expected}, got {train_base.classes}."
        )

    train_indices, validation_indices, test_indices = split_indices(
        len(train_base),
        validation_fraction=validation_fraction,
        test_fraction=test_fraction,
        seed=seed,
    )

    return EuroSATSplits(
        train=Subset(train_base, train_indices),
        validation=Subset(eval_base, validation_indices),
        test=Subset(eval_base, test_indices),
        classes=EUROSAT_CLASSES,
    )


def build_dataloaders(
    splits: EuroSATSplits,
    *,
    batch_size: int = 32,
    num_workers: int = 0,
    pin_memory: bool = False,
) -> dict[str, DataLoader[object]]:
    """Build DataLoaders using the project defaults."""
    common = {
        "batch_size": batch_size,
        "num_workers": num_workers,
        "pin_memory": pin_memory,
    }
    return {
        "train": DataLoader(splits.train, shuffle=True, **common),
        "validation": DataLoader(splits.validation, shuffle=False, **common),
        "test": DataLoader(splits.test, shuffle=False, **common),
    }


def load_rgb_image(path: Path) -> Image.Image:
    """Load one RGB image and close the underlying file descriptor safely."""
    with Image.open(path) as image:
        return image.convert("RGB")
