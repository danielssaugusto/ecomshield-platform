"""Offline checks for the new real-complaint annotation workflow."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("fsspec")
pytest.importorskip("openpyxl")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from prepare_consumerbr_pilot import (
    COMPANIES,
    choose_rows,
    normalized_key,
    sampling_key,
)
from validate_consumerbr_pilot_annotations import compare, validate_record


def test_selection_balances_companies_and_seals_reserved_ids() -> None:
    candidates = [
        {"sample_id": f"cbr-{company_no:02}-{i:03}", "company": company, "rank": sampling_key(f"{company_no}-{i}")}
        for company_no, company in enumerate(COMPANIES)
        for i in range(50)
    ]
    development, reserved, counts = choose_rows(candidates)
    assert len(development) == 240
    assert len(reserved) == 80
    assert {row["sample_id"] for row in development}.isdisjoint(row["sample_id"] for row in reserved)
    assert set(counts.values()) == {50}
    assert (development, reserved) == choose_rows(candidates)[:2]


def test_text_deduplication_normalizes_case_and_whitespace() -> None:
    assert normalized_key("  Produto   QUEBRADO\n") == normalized_key("produto quebrado")


def test_record_validation_does_not_invent_uncertain_intent() -> None:
    labels = {"cancel_order", "fora_de_escopo"}
    valid_uncertain = {"intent": "", "uncertain": "sim", "notes": "Dois pedidos concorrentes", "reviewer": "A"}
    assert validate_record(valid_uncertain, labels, require_complete=True) == []
    valid_clear = {"intent": "cancel_order", "uncertain": "não", "notes": "", "reviewer": "A"}
    assert validate_record(valid_clear, labels, require_complete=True) == []
    invalid = {"intent": "", "uncertain": "não", "notes": "", "reviewer": ""}
    assert set(validate_record(invalid, labels, require_complete=True)) == {
        "intenção vazia sem marca de incerteza", "revisor vazio"
    }


def test_comparison_flags_disagreement_and_uncertainty_without_adjudicating() -> None:
    a = [
        {"sample_id": "one", "intent": "cancel_order", "uncertain": "não", "notes": "pedido", "reviewer": "A"},
        {"sample_id": "two", "intent": "", "uncertain": "sim", "notes": "ambíguo", "reviewer": "A"},
    ]
    b = [
        {"sample_id": "one", "intent": "fora_de_escopo", "uncertain": "não", "notes": "outro", "reviewer": "B"},
        {"sample_id": "two", "intent": "", "uncertain": "sim", "notes": "ambíguo", "reviewer": "B"},
    ]
    decisions, summary = compare(a, b)
    assert summary == {
        "rows": 2,
        "different_intents": 1,
        "any_uncertain": 1,
        "needs_adjudication": 2,
        "human_ground_truth_complete": False,
    }
    assert all(row["needs_adjudication"] for row in decisions)
