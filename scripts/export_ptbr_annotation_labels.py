#!/usr/bin/env python3
"""Export label-only human annotation evidence from the two reviewed workbooks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from create_ptbr_validation_queue import stable_id
from download_b2w_reviews import SOURCE_SHA256 as B2W_SHA256


VALIDATED_FINAL_SHA256 = "36ddba3b620d73a86802a3863be0eb93dabcc2607b14ee4225f9e9d28b8cb8f0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True, help="XLSX com as duas opiniões.")
    parser.add_argument("--adjudication", type=Path, required=True, help="XLSX com as decisões finais.")
    parser.add_argument("--bitext", type=Path, default=Path("data/processed/bitext_retail_intents.parquet"))
    parser.add_argument("--output", type=Path, default=Path("data/annotations/ptbr_human_labels.csv"))
    args = parser.parse_args()

    reviews = pd.read_excel(args.reviews, sheet_name="Fila de anotação", dtype=str, keep_default_na=False)
    decisions = pd.read_excel(args.adjudication, sheet_name="Adjudicação", dtype=str, keep_default_na=False)
    required_reviews = {
        "sample_id", "feedback_text", "intent", "intent_second_opinion", "uncertain", "uncertain_second_opinion"
    }
    required_decisions = {"sample_id", "adjudicated_intent", "adjudication_notes"}
    if required_reviews.difference(reviews.columns) or required_decisions.difference(decisions.columns):
        raise ValueError("As planilhas não contêm as colunas esperadas de revisão e adjudicação.")
    if len(reviews) != 500 or not reviews["sample_id"].is_unique or not decisions["sample_id"].is_unique:
        raise ValueError("Esperavam-se 500 IDs únicos na revisão e IDs únicos na adjudicação.")
    if not reviews["sample_id"].eq(reviews["feedback_text"].map(stable_id)).all():
        raise ValueError("Um sample_id não corresponde ao hash do texto revisado.")
    if reviews[["intent", "intent_second_opinion"]].eq("").any().any():
        raise ValueError("Há votos humanos vazios.")
    allowed = set(pd.read_parquet(args.bitext, columns=["intent"])["intent"].astype(str))
    invalid = set(reviews["intent"]).union(reviews["intent_second_opinion"]).difference(allowed)
    if invalid:
        raise ValueError(f"Votos fora da taxonomia Bitext: {sorted(invalid)}")
    for name in ["uncertain", "uncertain_second_opinion"]:
        invalid_flags = set(reviews[name]).difference({"yes", "no"})
        if invalid_flags:
            raise ValueError(f"Valores inválidos em {name}: {sorted(invalid_flags)}")

    disagreements = reviews[reviews["intent"].ne(reviews["intent_second_opinion"])]
    if set(disagreements["sample_id"]) != set(decisions["sample_id"]):
        raise ValueError("A adjudicação não contém exatamente os IDs divergentes.")
    if decisions["adjudicated_intent"].eq("").any():
        raise ValueError("Ainda há decisões de adjudicação vazias.")
    invalid = set(decisions["adjudicated_intent"]).difference(allowed)
    if invalid:
        raise ValueError(f"Decisões fora da taxonomia Bitext: {sorted(invalid)}")

    labels = reviews[["sample_id", "intent", "intent_second_opinion", "uncertain", "uncertain_second_opinion"]].rename(
        columns={"intent": "intent_a", "intent_second_opinion": "intent_b", "uncertain": "uncertain_a", "uncertain_second_opinion": "uncertain_b"}
    )
    labels = labels.merge(decisions[["sample_id", "adjudicated_intent", "adjudication_notes"]], on="sample_id", how="left", validate="one_to_one")
    labels[["adjudicated_intent", "adjudication_notes"]] = labels[["adjudicated_intent", "adjudication_notes"]].fillna("")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    labels.to_csv(args.output, index=False)
    manifest = {
        "rows": len(labels),
        "double_agreement": len(labels) - len(decisions),
        "adjudicated": len(decisions),
        "review_workbook_sha256": sha256_file(args.reviews),
        "adjudication_workbook_sha256": sha256_file(args.adjudication),
        "b2w_source_sha256": B2W_SHA256,
        "labels_sha256": sha256_file(args.output),
        "final_csv_sha256": VALIDATED_FINAL_SHA256,
        "content": "Human votes and adjudication only; review text is reconstructed from the pinned B2W source.",
    }
    args.output.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Rótulos humanos exportados: {args.output} ({len(labels)} registros)")


if __name__ == "__main__":
    main()
