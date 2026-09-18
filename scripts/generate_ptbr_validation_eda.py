#!/usr/bin/env python3
"""Generate descriptive artifacts for the human-validated PT-BR dataset."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/ptbr_intent_validation_final.csv"))
    parser.add_argument("--report", type=Path, default=Path("reports/ptbr_intent_validation/eda_relatorio.md"))
    args = parser.parse_args()

    frame = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    required = {"sample_id", "validated_intent", "validation_method", "has_uncertainty_flag", "evaluation_eligible"}
    if missing := required.difference(frame.columns):
        raise ValueError(f"Dataset sem colunas necessárias: {sorted(missing)}")
    if len(frame) != frame["sample_id"].nunique() or frame["validated_intent"].eq("").any():
        raise ValueError("O dataset precisa ter um rótulo final não vazio e IDs únicos.")
    output = args.report.parent
    output.mkdir(parents=True, exist_ok=True)
    all_counts = frame["validated_intent"].value_counts().sort_values()
    eligible = frame[frame["evaluation_eligible"].eq("True")]
    eligible_counts = eligible["validated_intent"].value_counts().sort_values()
    uncertainty = pd.crosstab(frame["validated_intent"], frame["has_uncertainty_flag"]).reindex(columns=["False", "True"], fill_value=0)

    plt.figure(figsize=(10, 7))
    all_counts.plot.barh(color="#2563eb")
    plt.xlabel("Avaliações")
    plt.ylabel("Intenção validada")
    plt.title("Distribuição das intenções PT-BR validadas")
    plt.tight_layout()
    plt.savefig(output / "01_distribuicao_intencoes_validadas.png", dpi=160)
    plt.close()

    plt.figure(figsize=(7, 4))
    frame["validation_method"].value_counts().reindex(["double_agreement", "human_adjudication"]).plot.bar(color=["#0f766e", "#f59e0b"])
    plt.xlabel("Método de validação")
    plt.ylabel("Avaliações")
    plt.title("Origem do rótulo final")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output / "02_origem_rotulo_final.png", dpi=160)
    plt.close()

    uncertainty.sort_values("True").plot.barh(stacked=True, figsize=(10, 7), color=["#0f766e", "#dc2626"])
    plt.xlabel("Avaliações")
    plt.ylabel("Intenção validada")
    plt.title("Marca de incerteza por intenção")
    plt.legend(["Sem incerteza", "Com incerteza"])
    plt.tight_layout()
    plt.savefig(output / "03_incerteza_por_intencao.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 7))
    eligible_counts.plot.barh(color="#7c3aed")
    plt.xlabel("Avaliações elegíveis")
    plt.ylabel("Intenção validada")
    plt.title("Amostra elegível para avaliação externa")
    plt.tight_layout()
    plt.savefig(output / "04_amostra_elegivel_por_intencao.png", dpi=160)
    plt.close()

    rare = int((eligible_counts < 5).sum())
    args.report.write_text(
        f"""# EDA — validação humana PT-BR

## Escopo

Este relatório descreve a amostra B2W com rótulos humanos. Ela é um conjunto
externo de avaliação e não deve ser incorporada ao treinamento do baseline
Bitext. Essa separação preserva a validade da comparação futura.

## Integridade

- Avaliações com rótulo final: {len(frame):,}
- IDs únicos: {frame['sample_id'].nunique():,}
- Intenções observadas: {frame['validated_intent'].nunique():,} de 46 rótulos Bitext
- Rótulos por concordância dupla: {(frame['validation_method'] == 'double_agreement').sum():,}
- Rótulos por adjudicação: {(frame['validation_method'] == 'human_adjudication').sum():,}
- Registros com incerteza: {(frame['has_uncertainty_flag'] == 'True').sum():,}
- Registros elegíveis para métrica principal: {len(eligible):,}

## Interpretação responsável

A distribuição é concentrada: `submit_product_feedback` representa
{all_counts.get('submit_product_feedback', 0) / len(frame):.2%} do conjunto.
Entre os dados elegíveis, {rare} intenções têm menos de cinco exemplos. Por
isso, uma futura avaliação deve divulgar suporte por intenção e não apresentar
Macro F1 isoladamente como resultado conclusivo. O baseline atual é em inglês;
não se calcula desempenho dele neste conjunto PT-BR sem uma estratégia
linguística declarada e testada.

## Figuras

- `01_distribuicao_intencoes_validadas.png`
- `02_origem_rotulo_final.png`
- `03_incerteza_por_intencao.png`
- `04_amostra_elegivel_por_intencao.png`
""", encoding="utf-8")
    print(f"EDA PT-BR gerada: {args.report}")


if __name__ == "__main__":
    main()
