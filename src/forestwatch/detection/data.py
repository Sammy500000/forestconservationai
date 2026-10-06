"""Dataset adapter for the public Forest-Change benchmark."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ForestChangeExample:
    """One aligned before/after RGB pair and its binary forest-change mask."""

    image_before: Path
    image_after: Path
    change_mask: Path
    sample_id: str
    split: str

    def load(self) -> tuple[Image.Image, Image.Image, Image.Image]:
        """Load the aligned RGB pair and mask as independent images."""
        with Image.open(self.image_before) as before:
            before_image = before.convert("RGB")
        with Image.open(self.image_after) as after:
            after_image = after.convert("RGB")
        with Image.open(self.change_mask) as mask:
            change_image = mask.convert("L")
        return before_image, after_image, change_image


def discover_examples(dataset_root: Path, *, split: str = "test") -> list[ForestChangeExample]:
    """Discover aligned examples from images/<split>/{A,B,label}."""
    root = dataset_root.expanduser().resolve()
    split_root = root / "images" / split
    before_root = split_root / "A"
    after_root = split_root / "B"
    mask_root = split_root / "label"

    if not before_root.is_dir() or not after_root.is_dir() or not mask_root.is_dir():
        raise FileNotFoundError(
            f"Expected Forest-Change layout below {split_root}: A/, B/, label/"
        )

    examples: list[ForestChangeExample] = []
    for before_path in sorted(before_root.glob("*.png")):
        after_path = after_root / before_path.name
        mask_path = mask_root / before_path.name
        if after_path.is_file() and mask_path.is_file():
            examples.append(
                ForestChangeExample(
                    image_before=before_path,
                    image_after=after_path,
                    change_mask=mask_path,
                    sample_id=before_path.stem,
                    split=split,
                )
            )
    return examples
