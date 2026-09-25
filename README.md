# Forest Conservation AI

A reproducible, local-first research prototype for satellite-based forest-loss screening and priority-aware early warning.

The project follows the supplied project materials: use transfer learning for land-cover classification, compare imagery from different dates to identify candidate forest-to-nonforest transitions, and later connect those events to a publish/subscribe notification layer with prioritized routing.

## Phase 1 status

Phase 1 established the repository and runtime foundation.

## Phase 2 status — complete

Phase 2 implements the land-cover classification layer and the fastest reproducible evaluation path.

It provides:

- EuroSAT RGB download from the official Zenodo distribution, with an MD5 checksum check.
- Deterministic 80/10/10 train/validation/test splitting with seed `42`.
- ResNet50 model construction using torchvision.
- Loading of the public `cm93/resnet50-eurosat` ResNet50 checkpoint from Hugging Face in safetensors format.
- Correct handling of the checkpoint's class-logit order, which differs from the alphabetical `ImageFolder` order.
- Checkpoint-specific preprocessing (bicubic resize, center crop, and the checkpoint's recorded RGB mean/std).
- Reference-compatible ImageNet preprocessing and a short optional fine-tuning path from ImageNet weights.
- Accuracy, macro precision, macro recall, macro F1, classification report, and confusion-matrix generation.
- A network-free Phase 2 smoke verification script so the ML code can be validated before downloading data.

### Phase 2 data/model sources

The EuroSAT RGB dataset is the official 27,000-image RGB release from the EuroSAT project and Zenodo.

- Official project: https://github.com/phelber/EuroSAT
- Official dataset record: https://zenodo.org/records/7711810
- Public EuroSAT ResNet50 checkpoint: https://huggingface.co/cm93/resnet50-eurosat

The public checkpoint is used as the default fast path. Its model card identifies it as a ResNet50 fine-tuned on EuroSAT, with 10 classes and safetensors weights. The project also retains an optional fine-tuning script for a conventional ImageNet-to-EuroSAT transfer-learning run.

## Prerequisites

For Phase 1 only:

- Python 3.12+
- Git
- Docker Desktop with Docker Compose

For Phase 2 ML work:

- The same Python environment with the ML extra installed.
- Internet access for the first dataset/checkpoint download.
- A GPU is useful for optional fine-tuning but is not required for the code/smoke checks.

## Installation

Create and activate a virtual environment:

    python -m venv .venv

Windows PowerShell:

    .\.venv\Scripts\Activate.ps1

macOS/Linux:

    source .venv/bin/activate

Install Phase 2 dependencies:

    python -m pip install --upgrade pip
    python -m pip install -e ".[dev,ml]"

## Phase 2 verification

Run the network-free verification first:

    python scripts/verify_phase2.py

Expected output includes:

    Phase 2 smoke verification passed.
    ResNet50 output shape: (2, 10)
    Deterministic split: 21600 / 2700 / 2700
    Local safetensors load: passed

## Download EuroSAT RGB

Download the official RGB archive and extract it under `data/external/eurosat`:

    python scripts/download_eurosat.py

The resulting dataset contains the ten EuroSAT class directories.

## Evaluate the public EuroSAT ResNet50 checkpoint

Run:

    python scripts/evaluate_eurosat.py

The script downloads the dataset and public checkpoint if they are not cached, evaluates the held-out test split, and writes:

    artifacts/metrics/eurosat_metrics.json
    artifacts/metrics/eurosat_classification_report.csv
    artifacts/figures/eurosat_confusion_matrix.png

The public checkpoint uses its own recorded EuroSAT preprocessing statistics rather than ImageNet statistics. This is intentional: evaluation preprocessing must match the checkpoint that produced the weights.

## Optional conventional transfer-learning run

To reproduce the project reference's basic transfer-learning setup starting from ImageNet ResNet50 weights:

    python scripts/finetune_eurosat.py --epochs 10

For a fast local experiment, use a small epoch count:

    python scripts/finetune_eurosat.py --epochs 1

The default training mode freezes the ResNet50 backbone and trains only the final classifier head. Add `--unfreeze` only when a full fine-tuning run is actually needed.

## Phase 1 runtime and Docker

The existing Phase 1 health service and local Mosquitto broker remain unchanged:

    pytest
    python -m ruff check .
    python -m forestwatch

For Docker:

    docker compose up --build

The Phase 1 health endpoint is:

    http://localhost:8500/healthz

The local MQTT broker listens on:

    localhost:1883

The ML dependencies are deliberately optional so the Phase 1 application image does not need to install the large PyTorch stack.

## Project layout

    forestconservationai/
    ├── configs/
    │   ├── model.yaml
    │   ├── detection.yaml
    │   ├── network.yaml
    │   └── study_area.yaml
    ├── data/
    │   └── README.md
    ├── mosquitto/
    │   └── config/
    │       └── mosquitto.conf
    ├── scripts/
    │   ├── download_eurosat.py
    │   ├── evaluate_eurosat.py
    │   ├── finetune_eurosat.py
    │   ├── verify_phase1.py
    │   └── verify_phase2.py
    ├── src/
    │   └── forestwatch/
    │       ├── ml/
    │       │   ├── constants.py
    │       │   ├── data.py
    │       │   ├── evaluate.py
    │       │   ├── inference.py
    │       │   ├── model.py
    │       │   └── __init__.py
    │       └── ...
    └── tests/
        ├── test_config.py
        ├── test_events.py
        ├── test_health.py
        └── test_ml_phase2.py

## What Phase 2 does not do

Phase 2 intentionally does not implement Sentinel-2 acquisition, bi-temporal change detection, Hansen/GFW validation, MQTT routing, concurrent notifications, or the dashboard. Those are later phases.

## Next phase

Phase 3 will use a bi-temporal forest-change dataset to implement candidate forest-loss detection using the Phase 2 classifier.

## License

MIT. See LICENSE.
