"""Forest-Change benchmark dataset utilities for Phase 3.

The Forest-Change benchmark contains aligned bi-temporal RGB satellite
image pairs and binary forest-change masks. This module deliberately keeps
the dataset adapter independent of the model so that Phase 3 can remain
reproducible and lightweight.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ForestChangeExample:
    """One aligned before/after image pair and its binary change mask."""

    image_before: Path
    image_after: Path
    change_mask: Path
    sample_id: str

    def load(self) -> tuple[Image.Image, Image.Image, Image.Image]:
        """Load the aligned RGB pair and mask as independent PIL images."""
        with Image.open(self.image_before) as before:
            before_image = before.convert("RGB")
        with Image.open(self.image_after) as after:
            after_image = after.convert("RGB")
        with Image.open(self.change_mask) as mask:
            change_image = mask.convert("L")
        return before_image, after_image, change_image
