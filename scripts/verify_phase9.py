"""Final Phase 9 reproducibility and submission acceptance gate."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = (
    Path("README.md"),
    Path("LICENSE"),
    Path("pyproject.toml"),
    Path("docs/phase-8-plan.md"),
    Path("docs/phase-9-plan.md"),
    Path("scripts/verify_phase7.py"),
    Path("scripts/verify_phase8.py"),
    Path("scripts/validate_against_gfc.py"),
    Path("src/forestwatch/schemas/events.py"),
    Path("src/forestwatch/validation/gfc.py"),
)

REQUIRED_DIRECTORIES = (
    Path("artifacts/metrics"),
    Path("artifacts/figures"),
    Path("data/external"),
    Path("data/external/gfc"),
    Path("models"),
)

FORBIDDEN_TRACKED_PREFIXES = (
    "data/raw/",
    "data/processed/",
    "data/external/forest_change/",
    "data/external/gfc/",
)

FORBIDDEN_LARGE_SUFFIXES = (
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".tif",
    ".tiff",
    ".jp2",
    ".zip",
    ".tar",
    ".tar.gz",
)


def run(command: list[str]) -> None:
    """Run one acceptance command and fail on non-zero exit."""
    print("$", " ".join(command))
    subprocess.run(command, check=True)


def verify_repository_contract() -> None:
    """Check that the final repository contains the expected completion contract."""
    missing = [str(path) for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        raise AssertionError(f"Missing required files: {missing}")

    missing_dirs = [str(path) for path in REQUIRED_DIRECTORIES if not path.is_dir()]
    if missing_dirs:
        raise AssertionError(f"Missing required directories: {missing_dirs}")

    readme = Path("README.md").read_text(encoding="utf-8")
    phase9 = Path("docs/phase-9-plan.md").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    if "Phase 9" not in readme:
        raise AssertionError("README.md does not document Phase 9.")
    if "Phase 9" not in phase9:
        raise AssertionError("docs/phase-9-plan.md does not describe Phase 9.")
    if 'version = "0.9.0"' not in pyproject:
        raise AssertionError("Project version must be 0.9.0 at the Phase 9 completion gate.")

    git_files = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    violations: list[str] = []
    for path in git_files:
        normalized = path.replace("\\", "/")
        if normalized.startswith(FORBIDDEN_TRACKED_PREFIXES):
            if not normalized.endswith("/.gitkeep"):
                violations.append(normalized)
                continue
        if any(normalized.lower().endswith(suffix) for suffix in FORBIDDEN_LARGE_SUFFIXES):
            if normalized.startswith(("models/", "data/")):
                violations.append(normalized)

    if violations:
        raise AssertionError(
            "Large/downloaded runtime artifacts must not be tracked in Git: "
            f"{violations}"
        )


def main() -> int:
    """Run repository, test, lint, compilation, and prior-phase acceptance gates."""
    verify_repository_contract()
    run([sys.executable, "-m", "pytest"])
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "compileall", "-q", "src"])
    run([sys.executable, "scripts/verify_phase7.py"])
    run([sys.executable, "scripts/verify_phase8.py"])
    print("Phase 9 acceptance verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
