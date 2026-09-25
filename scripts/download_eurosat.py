from __future__ import annotations

import argparse
from pathlib import Path

from forestwatch.ml.data import download_eurosat


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the official EuroSAT RGB dataset.")
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("data/external/eurosat"),
        help="Directory in which EuroSAT_RGB will be created.",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing dataset.")
    args = parser.parse_args()

    summary = download_eurosat(args.destination, force=args.force)
    print(f"EuroSAT root: {summary.root}")
    print(f"Total images: {summary.total_images}")
    for class_name, count in summary.class_counts.items():
        print(f"  {class_name}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
