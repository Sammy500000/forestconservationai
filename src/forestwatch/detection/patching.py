"""Aligned patch extraction for bi-temporal forest-change pairs."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from PIL import Image


@dataclass(frozen=True)
class PatchPair:
    """One aligned pair of RGB patches plus its mask patch."""

    before: Image.Image
    after: Image.Image
    mask: Image.Image
    row: int
    column: int
    left: int
    top: int


def iter_aligned_patches(
    before: Image.Image,
    after: Image.Image,
    mask: Image.Image,
    *,
    patch_size: int = 64,
    include_partial: bool = False,
) -> list[PatchPair]:
    """Extract non-overlapping aligned patches from a bi-temporal example."""
    if patch_size <= 0:
        raise ValueError("patch_size must be positive")
    if before.size != after.size or before.size != mask.size:
        raise ValueError("before, after, and mask images must have identical dimensions")

    width, height = before.size
    row_starts = (
        range(0, height, patch_size)
        if include_partial
        else range(0, height - patch_size + 1, patch_size)
    )
    column_starts = (
        range(0, width, patch_size)
        if include_partial
        else range(0, width - patch_size + 1, patch_size)
    )

    patches: list[PatchPair] = []
    for row, top in enumerate(row_starts):
        for column, left in enumerate(column_starts):
            right = min(left + patch_size, width)
            bottom = min(top + patch_size, height)
            box = (left, top, right, bottom)
            before_patch = before.crop(box)
            after_patch = after.crop(box)
            mask_patch = mask.crop(box)

            if include_partial and (
                before_patch.size != (patch_size, patch_size)
                or after_patch.size != (patch_size, patch_size)
                or mask_patch.size != (patch_size, patch_size)
            ):
                padded_before = Image.new("RGB", (patch_size, patch_size))
                padded_after = Image.new("RGB", (patch_size, patch_size))
                padded_mask = Image.new("L", (patch_size, patch_size))
                padded_before.paste(before_patch, (0, 0))
                padded_after.paste(after_patch, (0, 0))
                padded_mask.paste(mask_patch, (0, 0))
                before_patch, after_patch, mask_patch = (
                    padded_before,
                    padded_after,
                    padded_mask,
                )

            patches.append(
                PatchPair(
                    before=before_patch,
                    after=after_patch,
                    mask=mask_patch,
                    row=row,
                    column=column,
                    left=left,
                    top=top,
                )
            )
    return patches


def expected_patch_count(width: int, height: int, patch_size: int = 64) -> int:
    """Return full non-overlapping patch count."""
    if patch_size <= 0:
        raise ValueError("patch_size must be positive")
    if width < patch_size or height < patch_size:
        return 0
    rows = ceil((height - patch_size + 1) / patch_size)
    columns = ceil((width - patch_size + 1) / patch_size)
    return rows * columns


def change_fraction(mask: Image.Image, *, threshold: int = 1) -> float:
    """Return the fraction of mask pixels considered changed."""
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be in [0, 255]")
    values = list(mask.convert("L").getdata())
    return sum(pixel >= threshold for pixel in values) / len(values) if values else 0.0
