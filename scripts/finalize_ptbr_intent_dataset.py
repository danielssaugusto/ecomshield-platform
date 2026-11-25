#!/usr/bin/env python3
"""Finalize the PT-BR validation dataset after human adjudication."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-workbook", type=Path, required=True)
    parser.add_argument("--adjudication-workbook", type=Path, required=True)
    parser.add_argument("--bitext-dataset", type=Path, default=Path("data/processed/bitext_retail_intents.parquet"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/ptbr_intent_validation_final.csv"))
    parser.add_argument("--report", type=Path, default=Path("reports/ptbr_intent_validation/final_relatorio.md"))
    args = parser.parse_args()

    source = pd.read_excel(args.source_workbook, sheet_name="Fila de anotação", dtype=str, keep_default_na=False)
    adjudication = pd.read_excel(args.adjudication_workbook, sheet_name="Adjudicação", dtype=str, keep_default_na=False)
    official = set(pd.read_parquet(args.bitext_dataset, columns=["intent"])["intent"].dropna().astype(str))
    source_required = {"sample_id", "feedback_text", "intent", "intent_second_opinion", "uncertain", "uncertain_second_opinion"}
    adjudication_required = {"sample_id", "adjudicated_intent", "adjudication_notes"}
    if missing := source_required.difference(source.columns):
        raise ValueError(f"Fonte sem colunas esperadas: {sorted(missing)}")
    if missing := adjudication_required.difference(adjudication.columns):
        raise ValueError(f"Adjudicação sem colunas esperadas: {sorted(missing)}")

    source["agreement"] = source["intent"].eq(source["intent_second_opinion"])
    expected_ids = set(source.loc[~source["agreement"], "sample_id"])
    adjudication = adjudication[["sample_id", "adjudicated_intent", "adjudication_notes"]].copy()
    if not adjudication["sample_id"].is_unique:
        raise ValueError("A planilha de adjudicação contém sample_id duplicado.")
    if expected_ids != set(adjudication["sample_id"]):
        raise ValueError("A planilha de adjudicação precisa conter exatamente os casos divergentes.")
    if adjudication["adjudicated_intent"].str.strip().eq("").any():
        raise ValueError("Ainda há decisões de adjudicação vazias.")
    invalid = sorted(set(adjudication["adjudicated_intent"]).difference(official))
    if invalid:
        raise ValueError(f"Há rótulos fora da taxonomia Bitext: {invalid}")

    final = source[["sample_id", "feedback_text", "intent", "intent_second_opinion", "uncertain", "uncertain_second_opinion", "agreement"]].copy()
    final = final.merge(adjudication, on="sample_id", how="left", validate="one_to_one")
    final["validated_intent"] = final["intent"].where(final["agreement"], final["adjudicated_intent"])
    final["validation_method"] = final["agreement"].map({True: "double_agreement", False: "human_adjudication"})
    final["has_uncertainty_flag"] = final[["uncertain", "uncertain_second_opinion"]].eq("yes").any(axis=1)
    final["evaluation_eligible"] = ~final["has_uncertainty_flag"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(args.output, index=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        f"""# Dataset PT-BR validado por revisão humana

- Registros finais: {len(final):,}
- Rótulos por concordância dupla: {int(final['agreement'].sum()):,}
- Rótulos por adjudicação: {int((~final['agreement']).sum()):,}
- Registros com marca de incerteza: {int(final['has_uncertainty_flag'].sum()):,}
- Registros elegíveis para a avaliação principal: {int(final['evaluation_eligible'].sum()):,}
- Taxonomia: 46 intenções originais do Bitext Retail eCommerce.

O arquivo final preserva as duas opiniões, a decisão de adjudicação quando
necessária e o método que originou cada rótulo validado.

Os registros com `has_uncertainty_flag=true` são preservados para auditoria,
mas ficam fora da métrica principal. O conjunto usa 20 das 46 intenções da
taxonomia, refletindo as intenções observadas nos feedbacks B2W selecionados.
""", encoding="utf-8")
    print(f"Dataset validado criado: {args.output}")


if __name__ == "__main__":
    main()
