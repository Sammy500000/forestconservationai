"""Optional validation helpers for external forest-loss reference data."""
from __future__ import annotations

from forestwatch.validation.gfc import (
    GFCValidationRecord,
    GFCValidationSummary,
    summarize_records,
    validate_event_bounds,
)

__all__ = [
    "GFCValidationRecord",
    "GFCValidationSummary",
    "summarize_records",
    "validate_event_bounds",
]
