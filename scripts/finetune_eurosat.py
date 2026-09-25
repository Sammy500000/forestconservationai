from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn, optim

from forestwatch.config import load_yaml_config
from forestwatch.logging import configure_logging
from forestwatch.ml.data import build_dataloaders, build_eurosat_splits, download_eurosat
from forestwatch.ml.model import build_resnet50, save_safetensors


def choose_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def run_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader[object],
    *,
    device: torch.device,
    optimizer: optim.Optimizer | None,
) -> tuple[float, float]:
    training = optimizer is not None
    model.train(training)
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images = images.to(device, non_blocking=device.type == "cuda")
        labels = labels.to(device, non_blocking=device.type == "cuda")

        if optimizer is not None:
            optimizer.zero_grad(set_to_none=True)

        with torch.set_grad_enabled(training):
            logits = model(images)
            loss = criterion(logits, labels)
            if optimizer is not None:
                loss.backward()
                optimizer.step()

        total_loss += float(loss.item()) * labels.size(0)
        correct += int((logits.argmax(dim=1) == labels).sum().item())
        total += labels.size(0)

    return total_loss / total, correct / total


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional quick EuroSAT ResNet50 fine-tuning run.")
    parser.add_argument("--data-root", type=Path, default=Path("data/external/eurosat"))
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("models/eurosat_resnet50_finetuned.safetensors"),
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--unfreeze",
        action="store_true",
        help="Fine-tune the whole model instead of only the classifier head.",
    )
    args = parser.parse_args()

    configure_logging()
    config = load_yaml_config("model.yaml")
    model_config = config["model"]
    training_config = config["training"]
    epochs = int(args.epochs or training_config["epochs"])
    device = choose_device()

    summary = download_eurosat(args.data_root)
    splits = build_eurosat_splits(
        summary.root,
        input_size=int(model_config["input_size"]),
        validation_fraction=float(training_config["validation_fraction"]),
        test_fraction=float(training_config["test_fraction"]),
        seed=int(training_config["seed"]),
    )
    loaders = build_dataloaders(
        splits,
        batch_size=int(training_config["batch_size"]),
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )

    model = build_resnet50(
        num_classes=int(model_config["num_classes"]),
        imagenet_pretrained=True,
        freeze_backbone=not args.unfreeze,
    ).to(device)

    parameters = model.parameters() if args.unfreeze else model.fc.parameters()
    optimizer = optim.Adam(parameters, lr=float(training_config["learning_rate"]))

    best_accuracy = -1.0
    for epoch in range(1, epochs + 1):
        train_loss, train_accuracy = run_epoch(
            model,
            loaders["train"],
            device=device,
            optimizer=optimizer,
        )
        validation_loss, validation_accuracy = run_epoch(
            model,
            loaders["validation"],
            device=device,
            optimizer=None,
        )
        print(
            f"Epoch {epoch}/{epochs} | train loss={train_loss:.4f} "
            f"acc={train_accuracy:.4f} | val loss={validation_loss:.4f} "
            f"acc={validation_accuracy:.4f}"
        )
        if validation_accuracy > best_accuracy:
            best_accuracy = validation_accuracy
            save_safetensors(model, args.output)

    print(f"Best validation accuracy: {best_accuracy:.4f}")
    print(f"Saved checkpoint: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
