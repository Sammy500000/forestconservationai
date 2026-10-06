from __future__ import annotations

import subprocess
from pathlib import Path


def test_phase9_plan_exists() -> None:
    path = Path("docs/phase-9-plan.md")
    assert path.is_file()
    assert "Final Reproducibility and Submission Package" in path.read_text(encoding="utf-8")


def test_phase9_verifier_declares_completion_gate() -> None:
    path = Path("scripts/verify_phase9.py")
    assert path.is_file()
    source = path.read_text(encoding="utf-8")
    for command in (
        "verify_phase7.py",
        "verify_phase8.py",
        "ruff",
        "compileall",
        "pytest",
    ):
        assert command in source


def test_phase9_branch_is_cleanly_buildable() -> None:
    result = subprocess.run(
        ["python", "-m", "compileall", "-q", "src"],
        check=False,
    )
    assert result.returncode == 0
