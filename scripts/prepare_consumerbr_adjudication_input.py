"""Create a private, minimal input for adjudicating flagged ConsumerBR rows."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "outputs/tp3-consumerbr"


def main() -> None:
    source_path = PRIVATE / "pilot_development.csv"
    comparison_path = PRIVATE / "pilot_annotation_comparison.csv"
    output_path = PRIVATE / "adjudication_input.json"
    with source_path.open(encoding="utf-8", newline="") as source_file:
        source = {row["sample_id"]: row["complaint_text"] for row in csv.DictReader(source_file)}
    with comparison_path.open(encoding="utf-8", newline="") as comparison_file:
        flagged = [row for row in csv.DictReader(comparison_file) if row["needs_adjudication"] == "True"]
    records = []
    for row in flagged:
        records.append({
            "sample_id": row["sample_id"],
            "complaint_text": source[row["sample_id"]],
            "intent_a": row["intent_a"],
            "uncertain_a": row["uncertain_a"],
            "notes_a": row["notes_a"],
            "reviewer_a": row["reviewer_a"],
            "intent_b": row["intent_b"],
            "uncertain_b": row["uncertain_b"],
            "notes_b": row["notes_b"],
            "reviewer_b": row["reviewer_b"],
        })
    if len(records) != 167 or len({row["sample_id"] for row in records}) != len(records):
        raise ValueError("A comparação deve conter 167 IDs únicos para adjudicação.")
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Entrada privada de adjudicação criada: {len(records)} casos.")


if __name__ == "__main__":
    main()
