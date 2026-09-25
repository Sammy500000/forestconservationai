from __future__ import annotations

from typing import Final

EUROSAT_CLASSES: Final[tuple[str, ...]] = (
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

# The public EuroSAT checkpoint stores logits in this exact order.
EUROSAT_CHECKPOINT_CLASSES: Final[tuple[str, ...]] = (
    "Forest",
    "River",
    "Highway",
    "AnnualCrop",
    "SeaLake",
    "HerbaceousVegetation",
    "Industrial",
    "Residential",
    "PermanentCrop",
    "Pasture",
)

EUROSAT_ZIP_URL: Final[str] = (
    "https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1"
)
EUROSAT_ZIP_MD5: Final[str] = "f46e308c4d50d4bf32fedad2d3d62f3b"

EUROSAT_HF_MODEL_ID: Final[str] = "cm93/resnet50-eurosat"
EUROSAT_HF_MODEL_FILENAME: Final[str] = "model.safetensors"
EUROSAT_HF_MODEL_REVISION: Final[str] = "main"

IMAGENET_MEAN: Final[tuple[float, float, float]] = (0.485, 0.456, 0.406)
IMAGENET_STD: Final[tuple[float, float, float]] = (0.229, 0.224, 0.225)

# Preprocessing used to produce the public cm93/resnet50-eurosat checkpoint.
CHECKPOINT_MEAN: Final[tuple[float, float, float]] = (0.3445, 0.3803, 0.4077)
CHECKPOINT_STD: Final[tuple[float, float, float]] = (0.0915, 0.0652, 0.0553)
