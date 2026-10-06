from __future__ import annotations

import pytest

from forestwatch.validation.gfc import GFCValidationRecord, summarize_records


def test_summary_empty() -> None:
    summary = summarize_records([])
    assert summary.candidate_count == 0
    assert summary.candidates_with_loss == 0
    assert summary.agreement_rate == 0.0


def test_summary_agreement_rate() -> None:
    records = (
        GFCValidationRecord("EVT-1", 0.5, True, 2024, 2024),
        GFCValidationRecord("EVT-2", 0.0, False, None, None),
        GFCValidationRecord("EVT-3", 0.25, True, 2022, 2023),
    )
    summary = summarize_records(records)
    assert summary.candidate_count == 3
    assert summary.candidates_with_loss == 2
    assert summary.agreement_rate == pytest.approx(2 / 3)
    assert summary.mean_loss_fraction == pytest.approx(0.25)


def test_record_is_immutable() -> None:
    record = GFCValidationRecord("EVT", 0.2, True, 2024, 2024)
    with pytest.raises(Exception):
        record.event_id = "changed"  # type: ignore[misc]
