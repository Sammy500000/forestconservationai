from __future__ import annotations

import tempfile
from pathlib import Path

import torch
from PIL import Image
from safetensors.torch import save_file

from forestwatch.ml.constants import EUROSAT_CLASSES
from forestwatch.ml.data import build_eval_transform, split_indices
from forestwatch.ml.model import build_resnet50, load_local_safetensors


def main() -> int:
    model = build_resnet50(num_classes=len(EUROSAT_CLASSES))
    model.eval()

    batch = torch.zeros((2, 3, 224, 224), dtype=torch.float32)
    with torch.inference_mode():
        output = model(batch)
    assert tuple(output.shape) == (2, len(EUROSAT_CLASSES))

    image = Image.new("RGB", (64, 64), color=(64, 128, 64))
    transformed = build_eval_transform(224)(image)
    assert tuple(transformed.shape) == (3, 224, 224)

    train, validation, test = split_indices(27_000, seed=42)
    assert (len(train), len(validation), len(test)) == (21_600, 2_700, 2_700)
    assert len(set(train) | set(validation) | set(test)) == 27_000

    with tempfile.TemporaryDirectory(prefix="forestwatch-phase2-") as temp_dir:
        checkpoint = Path(temp_dir) / "smoke.safetensors"
        save_file(
            {key: value.detach().cpu().contiguous() for key, value in model.state_dict().items()},
            str(checkpoint),
        )
        loaded = build_resnet50(num_classes=len(EUROSAT_CLASSES))
        load_local_safetensors(loaded, checkpoint)

    print("Phase 2 smoke verification passed.")
    print(f"Classes: {', '.join(EUROSAT_CLASSES)}")
    print("ResNet50 output shape: (2, 10)")
    print("Deterministic split: 21600 / 2700 / 2700")
    print("Local safetensors load: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
