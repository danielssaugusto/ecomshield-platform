#!/usr/bin/env python3
"""Validate two independent human annotation files and calculate agreement."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score


REQUIRED_COLUMNS = {"sample_id", "feedback_text", "intent", "uncertain", "notes"}


def read_annotations(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} não contém as colunas obrigatórias: {sorted(missing)}")
    if not frame["sample_id"].is_unique:
        raise ValueError(f"{path} contém sample_id duplicado.")
    return frame


def read_workbook_annotations(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the formatted workbook containing both independent reviews."""
    frame = pd.read_excel(path, sheet_name="Fila de anotação", dtype=str, keep_default_na=False)
    base_columns = ["sample_id", "feedback_text", "intent", "uncertain", "notes"]
    second_columns = ["sample_id", "feedback_text", "intent_second_opinion", "uncertain_second_opinion", "notes_second_opinion"]
    missing = set(base_columns + second_columns).difference(frame.columns)
    if missing:
        raise ValueError(f"Planilha sem as colunas esperadas: {sorted(missing)}")
    first = frame[base_columns].copy()
    second = frame[second_columns].rename(columns={
        "intent_second_opinion": "intent",
        "uncertain_second_opinion": "uncertain",
        "notes_second_opinion": "notes",
    })
    return first, second


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--workbook", type=Path, help="XLSX com intent e intent_second_opinion.")
    source_group.add_argument("--annotator-a", type=Path, help="CSV da primeira anotação.")
    parser.add_argument("--annotator-b", type=Path, help="CSV da segunda anotação; obrigatório com --annotator-a.")
    parser.add_argument("--output", type=Path, default=Path("data/annotations/ptbr_intent_adjudication.csv"))
    parser.add_argument("--report", type=Path, default=Path("reports/ptbr_intent_validation/relatorio.md"))
    parser.add_argument("--bitext-dataset", type=Path, default=Path("data/processed/bitext_retail_intents.parquet"))
    args = parser.parse_args()

    if args.workbook:
        first, second = read_workbook_annotations(args.workbook)
    else:
        if args.annotator_b is None:
            parser.error("--annotator-b é obrigatório quando --annotator-a é usado.")
        first, second = read_annotations(args.annotator_a), read_annotations(args.annotator_b)
    a = first.rename(columns={"intent": "intent_a", "uncertain": "uncertain_a", "notes": "notes_a"})
    b = second.rename(columns={"intent": "intent_b", "uncertain": "uncertain_b", "notes": "notes_b"})
    official_intents = set(pd.read_parquet(args.bitext_dataset, columns=["intent"])["intent"].dropna().astype(str))
    merged = a.merge(b[["sample_id", "intent_b", "uncertain_b", "notes_b"]], on="sample_id", how="outer", indicator=True, validate="one_to_one")
    if not (merged["_merge"] == "both").all():
        raise ValueError("As filas A e B precisam conter exatamente os mesmos sample_id.")
    if not (merged["intent_a"].str.strip().ne("") & merged["intent_b"].str.strip().ne("")).all():
        raise ValueError("Há intenções vazias. Complete as duas revisões antes da validação.")
    used_intents = set(merged["intent_a"]).union(merged["intent_b"])
    invalid_intents = sorted(used_intents.difference(official_intents))
    if invalid_intents:
        raise ValueError(f"Há rótulos fora da taxonomia original do Bitext: {invalid_intents}")

    merged["agreement"] = merged["intent_a"].eq(merged["intent_b"])
    merged["adjudicated_intent"] = merged["intent_a"].where(merged["agreement"], "")
    merged["adjudication_notes"] = ""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged.drop(columns="_merge").to_csv(args.output, index=False)

    kappa = cohen_kappa_score(merged["intent_a"], merged["intent_b"])
    agreement = float(merged["agreement"].mean())
    disagreements = merged.loc[~merged["agreement"], ["sample_id", "feedback_text", "intent_a", "intent_b"]]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        f"""# Validação humana de intenções em PT-BR

## Resultado da dupla anotação

- Registros avaliados: {len(merged):,}
- Concordância simples: {agreement:.2%}
- Cohen's kappa: {kappa:.4f}
- Registros para adjudicação: {len(disagreements):,}

Os registros divergentes estão no arquivo de adjudicação. Os registros com
concordância recebem automaticamente o mesmo valor em `adjudicated_intent`.
Nenhum registro divergente é considerado validado até receber um
`adjudicated_intent` após a revisão.
""", encoding="utf-8")
    print(json.dumps({"rows": len(merged), "agreement": agreement, "cohen_kappa": kappa, "disagreements": len(disagreements)}))


if __name__ == "__main__":
    main()
