"""Optional validation helpers for external forest-loss reference data."""
from __future__ import annotations

from forestwatch.validation.gfc import GFCValidationRecord, validate_detections_against_gfc

__all__ = ["GFCValidationRecord", "validate_detections_against_gfc"]
