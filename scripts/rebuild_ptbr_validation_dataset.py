#!/usr/bin/env python3
"""Rebuild the PT-BR validation dataset from B2W and versioned human labels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from create_ptbr_validation_queue import select_sample, stable_id
from download_b2w_reviews import DEFAULT_PATH, ensure_b2w_source


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--b2w", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--labels", type=Path, default=Path("data/annotations/ptbr_human_labels.csv"))
    parser.add_argument("--manifest", type=Path, default=Path("data/annotations/ptbr_human_labels.manifest.json"))
    parser.add_argument("--bitext", type=Path, default=Path("data/processed/bitext_retail_intents.parquet"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/ptbr_intent_validation_final.csv"))
    parser.add_argument("--report", type=Path, default=Path("reports/ptbr_intent_validation/final_relatorio.md"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if sha256_file(args.labels) != manifest["labels_sha256"]:
        raise ValueError("O CSV de decisões humanas não corresponde ao manifesto.")
    source = ensure_b2w_source(args.b2w)
    if sha256_file(source) != manifest["b2w_source_sha256"]:
        raise ValueError("O B2W não corresponde à fonte usada na anotação.")
    raw = pd.read_csv(source, low_memory=False)
    sample = select_sample(raw)
    sample["sample_id"] = sample["feedback_text"].map(stable_id)
    labels = pd.read_csv(args.labels, dtype=str, keep_default_na=False)
    required = {"sample_id", "intent_a", "intent_b", "uncertain_a", "uncertain_b", "adjudicated_intent", "adjudication_notes"}
    if required.difference(labels.columns) or len(labels) != 500 or not labels["sample_id"].is_unique:
        raise ValueError("O arquivo de anotações precisa ter 500 IDs únicos e todas as colunas esperadas.")
    if set(labels["sample_id"]) != set(sample["sample_id"]):
        raise ValueError("Os IDs anotados não correspondem à amostra B2W reproduzida.")
    if labels[["intent_a", "intent_b"]].eq("").any().any():
        raise ValueError("Há votos humanos vazios.")
    allowed = set(pd.read_parquet(args.bitext, columns=["intent"])["intent"].astype(str))
    used = set(labels["intent_a"]).union(labels["intent_b"])
    if used.difference(allowed):
        raise ValueError(f"Rótulos humanos fora da taxonomia Bitext: {sorted(used.difference(allowed))}")
    for flag in ["uncertain_a", "uncertain_b"]:
        if set(labels[flag]).difference({"yes", "no"}):
            raise ValueError(f"Valores inválidos na coluna {flag}.")
    disagreement = labels["intent_a"].ne(labels["intent_b"])
    if labels.loc[disagreement, "adjudicated_intent"].eq("").any():
        raise ValueError("Há divergências sem adjudicação.")
    if set(labels.loc[disagreement, "adjudicated_intent"]).difference(allowed):
        raise ValueError("Há decisões de adjudicação fora da taxonomia Bitext.")

    final = labels.merge(sample[["sample_id", "feedback_text"]], on="sample_id", how="left", validate="one_to_one")
    final["agreement"] = ~disagreement.to_numpy()
    final["validated_intent"] = final["intent_a"].where(final["agreement"], final["adjudicated_intent"])
    final["validation_method"] = final["agreement"].map({True: "double_agreement", False: "human_adjudication"})
    final["has_uncertainty_flag"] = final[["uncertain_a", "uncertain_b"]].eq("yes").any(axis=1)
    final["evaluation_eligible"] = ~final["has_uncertainty_flag"]
    final = final.rename(columns={"intent_a": "intent", "intent_b": "intent_second_opinion", "uncertain_a": "uncertain", "uncertain_b": "uncertain_second_opinion"})
    final = final[["sample_id", "feedback_text", "intent", "intent_second_opinion", "uncertain", "uncertain_second_opinion", "agreement", "adjudicated_intent", "adjudication_notes", "validated_intent", "validation_method", "has_uncertainty_flag", "evaluation_eligible"]]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(args.output, index=False)
    actual_final_hash = sha256_file(args.output)
    if actual_final_hash != manifest["final_csv_sha256"]:
        raise ValueError(f"O dataset final difere da versão validada: {actual_final_hash}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        f"""# Dataset PT-BR validado por revisão humana

- Registros finais: {len(final):,}
- Rótulos por concordância dupla: {int(final['agreement'].sum()):,}
- Rótulos por adjudicação: {int((~final['agreement']).sum()):,}
- Registros com marca de incerteza: {int(final['has_uncertainty_flag'].sum()):,}
- Registros elegíveis para a avaliação principal: {int(final['evaluation_eligible'].sum()):,}
- Taxonomia: 46 intenções originais do Bitext Retail eCommerce.
- SHA-256 do CSV reconstruído: `{actual_final_hash}`.

O arquivo final preserva as duas opiniões, a decisão de adjudicação quando
necessária e o método que originou cada rótulo validado.

Os registros com `has_uncertainty_flag=true` são preservados para auditoria,
mas ficam fora da métrica principal. O conjunto usa {final['validated_intent'].nunique()}
das 46 intenções da taxonomia. A amostra foi estratificada por nota e não
representa a distribuição operacional de chamados de atendimento.
""", encoding="utf-8")
    print(f"Dataset PT-BR reconstruído: {args.output} ({len(final)} registros)")


if __name__ == "__main__":
    main()
