from __future__ import annotations

import argparse
from pathlib import Path

import torch

from forestwatch.config import load_yaml_config
from forestwatch.logging import configure_logging
from forestwatch.ml.constants import EUROSAT_CHECKPOINT_CLASSES
from forestwatch.ml.data import (
    build_checkpoint_eval_transform,
    build_dataloaders,
    build_eurosat_splits,
    download_eurosat,
)
from forestwatch.ml.evaluate import (
    evaluate_model,
    save_classification_report,
    save_confusion_matrix,
    save_metrics,
)
from forestwatch.ml.model import build_resnet50, load_eurosat_checkpoint, load_local_safetensors


def choose_device(requested: str) -> torch.device:
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but no CUDA device is available.")
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the EuroSAT ResNet50 classifier.")
    parser.add_argument("--data-root", type=Path, default=Path("data/external/eurosat"))
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Local safetensors checkpoint. Defaults to the public EuroSAT checkpoint.",
    )
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    configure_logging()
    config = load_yaml_config("model.yaml")
    model_config = config["model"]
    checkpoint_config = config["checkpoint"]
    training_config = config["training"]
    device = choose_device(args.device)

    summary = download_eurosat(args.data_root)
    print(f"Using EuroSAT at {summary.root} ({summary.total_images} images).")

    splits = build_eurosat_splits(
        summary.root,
        input_size=int(model_config["input_size"]),
        validation_fraction=float(training_config["validation_fraction"]),
        test_fraction=float(training_config["test_fraction"]),
        seed=int(training_config["seed"]),
        eval_transform=build_checkpoint_eval_transform(),
    )
    loaders = build_dataloaders(
        splits,
        batch_size=int(training_config["batch_size"]),
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )

    model = build_resnet50(num_classes=int(model_config["num_classes"]))
    if args.checkpoint is not None:
        model = load_local_safetensors(model, args.checkpoint)
        checkpoint_description = str(args.checkpoint)
    else:
        checkpoint_dir = Path("models/cache")
        model = load_eurosat_checkpoint(
            model,
            model_id=str(checkpoint_config["repo_id"]),
            filename=str(checkpoint_config["filename"]),
            revision=str(checkpoint_config["revision"]),
            cache_dir=checkpoint_dir,
        )
        checkpoint_description = (
            f"hf://{checkpoint_config['repo_id']}@{checkpoint_config['revision']}/"
            f"{checkpoint_config['filename']}"
        )

    model = model.to(device)
    result = evaluate_model(
        model,
        loaders["test"],
        device=device,
        model_class_names=EUROSAT_CHECKPOINT_CLASSES,
    )

    metrics_dir = args.output_dir / "metrics"
    figures_dir = args.output_dir / "figures"
    save_metrics(result, metrics_dir / "eurosat_metrics.json")
    save_classification_report(result, metrics_dir / "eurosat_classification_report.csv")
    save_confusion_matrix(result, figures_dir / "eurosat_confusion_matrix.png")

    print(f"Checkpoint: {checkpoint_description}")
    print(f"Device: {device}")
    print(f"Test samples: {result.sample_count}")
    print(f"Accuracy: {result.accuracy:.4f}")
    print(f"Macro precision: {result.macro_precision:.4f}")
    print(f"Macro recall: {result.macro_recall:.4f}")
    print(f"Macro F1: {result.macro_f1:.4f}")
    print(f"Metrics: {metrics_dir / 'eurosat_metrics.json'}")
    print(f"Confusion matrix: {figures_dir / 'eurosat_confusion_matrix.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
