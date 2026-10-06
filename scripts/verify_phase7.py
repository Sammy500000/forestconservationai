"""Final acceptance verification for the ForestWatch Phase 7 deliverables."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import torch

from forestwatch.config import load_yaml_config
from forestwatch.detection.change_detection import ChangePrediction, build_candidate_change
from forestwatch.detection.patching import change_fraction, iter_aligned_patches
from forestwatch.ml.constants import EUROSAT_CHECKPOINT_CLASSES, EUROSAT_CLASSES
from forestwatch.ml.data import split_indices
from forestwatch.ml.model import build_resnet50
from forestwatch.networking.demo import build_demo_events, run_demo
from forestwatch.networking.priority import PriorityEventQueue
from forestwatch.networking.router import PriorityRouter
from forestwatch.networking.topology import build_default_topology


def run(command: list[str]) -> None:
    """Run a repository verification command and fail on non-zero status."""
    print("$", " ".join(command))
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def verify_configuration() -> None:
    """Validate that the committed configuration remains internally coherent."""
    model = load_yaml_config("model.yaml")["model"]
    detection = load_yaml_config("detection.yaml")["detection"]
    network = load_yaml_config("network.yaml")["network"]

    assert model["name"] == "resnet50"
    assert int(model["num_classes"]) == 10
    assert set(EUROSAT_CLASSES) == set(EUROSAT_CHECKPOINT_CLASSES)
    assert detection["forest_class"] == "Forest"
    assert "AnnualCrop" in detection["target_non_forest_classes"]
    assert float(detection["confidence_threshold"]) == 0.70
    assert int(detection["patch_size_pixels"]) == 64
    assert network["routing"]["algorithm"].lower() == "dijkstra"
    assert network["priorities"] == {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }


def verify_model_smoke() -> None:
    """Verify model construction and deterministic EuroSAT split behavior."""
    model = build_resnet50(num_classes=10)
    output = model(torch.zeros((1, 3, 224, 224)))
    assert tuple(output.shape) == (1, 10)

    train, validation, test = split_indices(27_000, seed=42)
    assert (len(train), len(validation), len(test)) == (21_600, 2_700, 2_700)
    assert not (set(train) & set(validation))
    assert not (set(train) & set(test))
    assert not (set(validation) & set(test))


def verify_detection_smoke() -> None:
    """Verify aligned patch extraction and forest-loss candidate logic."""
    from PIL import Image

    before = Image.new("RGB", (256, 256), (20, 80, 30))
    after = Image.new("RGB", (256, 256), (170, 120, 60))
    mask = Image.new("L", (256, 256), 0)
    mask.paste(255, (0, 0, 128, 128))

    patches = iter_aligned_patches(before, after, mask, patch_size=64)
    assert len(patches) == 16
    assert change_fraction(patches[0].mask) == 1.0

    candidate = build_candidate_change(
        ChangePrediction("Forest", 0.92, "AnnualCrop", 0.88),
        row=0,
        column=0,
        confidence_threshold=0.70,
    )
    assert candidate is not None
    assert candidate.confidence == 0.88


def verify_networking() -> None:
    """Verify priority ordering, shortest path, and deterministic concurrent delivery."""
    events = build_demo_events()
    queue = PriorityEventQueue()
    for event in reversed(events):
        queue.put(event)

    assert [queue.get().priority.name for _ in range(4)] == [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ]

    router = PriorityRouter(build_default_topology())
    route = router.route(
        events[0],
        source="forest_hub",
        destination="control_room",
    ).route
    assert route.path == ("forest_hub", "node_b", "district", "control_room")
    assert route.cost == 8.0

    result = __import__("asyncio").run(run_demo())
    assert result["ordered_priorities"] == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert float(result["metrics"].delivery_rate) == 1.0


def verify_artifact_contract() -> None:
    """Verify that generated research outputs have documented destination directories."""
    for directory in (
        Path("artifacts/metrics"),
        Path("artifacts/figures"),
        Path("models"),
        Path("data/external"),
    ):
        assert directory.is_dir(), f"Missing expected directory: {directory}"


def main() -> int:
    """Run final static, smoke, integration, and artifact checks."""
    run([sys.executable, "-m", "pytest"])
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "compileall", "-q", "src"])
    verify_configuration()
    verify_model_smoke()
    verify_detection_smoke()
    verify_networking()
    verify_artifact_contract()
    print("Phase 7 acceptance verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
