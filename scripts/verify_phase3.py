from __future__ import annotations

from PIL import Image

from forestwatch.detection.change_detection import ChangePrediction, build_candidate_change
from forestwatch.detection.patching import change_fraction, iter_aligned_patches


def main() -> int:
    before = Image.new("RGB", (256, 256), (20, 80, 30))
    after = Image.new("RGB", (256, 256), (170, 120, 60))
    mask = Image.new("L", (256, 256), 0)
    mask.paste(255, (0, 0, 128, 128))

    patches = iter_aligned_patches(before, after, mask, patch_size=64)
    assert len(patches) == 16
    assert change_fraction(patches[0].mask) == 1.0
    assert change_fraction(patches[-1].mask) == 0.0

    positive = build_candidate_change(
        ChangePrediction("Forest", 0.90, "AnnualCrop", 0.80),
        row=0,
        column=0,
    )
    assert positive is not None
    assert positive.confidence == 0.80

    negative = build_candidate_change(
        ChangePrediction("Forest", 0.69, "AnnualCrop", 0.90),
        row=0,
        column=1,
    )
    assert negative is None

    print("Phase 3 smoke verification passed.")
    print("Aligned 256x256 pair -> 16 x 64x64 patches: passed")
    print("Binary change-mask fraction: passed")
    print("Forest -> non-forest candidate rule: passed")
    print("Confidence threshold handling: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
