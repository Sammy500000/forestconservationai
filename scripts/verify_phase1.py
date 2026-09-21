from __future__ import annotations

import subprocess
import sys


def run(command: list[str]) -> None:
    print("$", " ".join(command))
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    run([sys.executable, "-m", "pytest"])
    run([sys.executable, "-m", "ruff", "check", "."])
    print("Phase 1 verification passed.")


if __name__ == "__main__":
    main()
