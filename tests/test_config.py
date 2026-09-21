from pathlib import Path

import pytest

from forestwatch.config import load_yaml_config


def test_all_phase1_configs_exist() -> None:
    expected = {"model.yaml", "detection.yaml", "network.yaml", "study_area.yaml"}
    config_dir = Path(__file__).resolve().parents[1] / "configs"
    assert {path.name for path in config_dir.glob("*.yaml")} == expected


def test_model_config_is_valid_mapping() -> None:
    config = load_yaml_config("model.yaml")
    assert config["model"]["name"] == "resnet50"
    assert config["model"]["num_classes"] == 10
    assert config["training"]["batch_size"] == 32


def test_detection_config_matches_reference_scope() -> None:
    config = load_yaml_config("detection.yaml")
    detection = config["detection"]

    assert detection["forest_class"] == "Forest"
    assert set(detection["target_non_forest_classes"]) == {
        "AnnualCrop",
        "Pasture",
        "Industrial",
        "Residential",
    }
    assert detection["patch_size_pixels"] == 64
    assert detection["sentinel_resolution_meters"] == 10


def test_network_config_contains_priority_order() -> None:
    config = load_yaml_config("network.yaml")
    priorities = config["network"]["priorities"]

    assert priorities["CRITICAL"] == 0
    assert priorities["HIGH"] == 1
    assert priorities["MEDIUM"] == 2
    assert priorities["LOW"] == 3
    assert config["network"]["routing"]["algorithm"] == "dijkstra"


def test_loader_rejects_path_traversal_and_non_yaml() -> None:
    with pytest.raises(ValueError):
        load_yaml_config("../configs/model.yaml")

    with pytest.raises(ValueError):
        load_yaml_config("model.txt")
