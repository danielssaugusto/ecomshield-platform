#!/usr/bin/env python3
"""Train and evaluate a transparent Bitext intent-classification baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/bitext_retail_intents.parquet"))
    parser.add_argument("--model", type=Path, default=Path("models/bitext_intent_tfidf_logreg.joblib"))
    parser.add_argument("--report-json", type=Path, default=Path("data/processed/bitext_intent_evaluation.json"))
    parser.add_argument("--report-md", type=Path, default=Path("reports/bitext_intent_model/relatorio.md"))
    parser.add_argument("--error-report", type=Path, default=Path("reports/bitext_intent_model/erros.md"))
    args = parser.parse_args()

    frame = pd.read_parquet(args.dataset)
    train = frame[frame["split"] == "train"]
    test = frame[frame["split"] == "test"]
    if train.empty or test.empty:
        raise ValueError("O dataset precisa conter as partições train e test.")

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=100_000)),
        ("classifier", LogisticRegression(max_iter=3_000, C=4.0, random_state=42)),
    ])
    model.fit(train["text"], train["intent"])
    predictions = model.predict(test["text"])
    report = classification_report(test["intent"], predictions, output_dict=True, zero_division=0)
    results = {
        "dataset": "bitext-retail-ecommerce-intents-v1",
        "model": "TF-IDF (1,2-gram) + LogisticRegression",
        "train_rows": len(train),
        "test_rows": len(test),
        "accuracy": accuracy_score(test["intent"], predictions),
        "macro_f1": f1_score(test["intent"], predictions, average="macro"),
        "weighted_f1": f1_score(test["intent"], predictions, average="weighted"),
        "per_intent": report,
        "limitation": "The Bitext corpus is English and hybrid/synthetic. Test performance measures in-distribution generalization only; it is not a production or PT-BR performance claim.",
    }
    args.model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model)
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text(
        f"""# Avaliação do baseline de intenção

- Modelo: TF-IDF (1–2 gramas) + Regressão Logística
- Treino/teste: {len(train):,}/{len(test):,} registros
- Accuracy: {results['accuracy']:.4f}
- Macro F1: {results['macro_f1']:.4f}
- Weighted F1: {results['weighted_f1']:.4f}

## Interpretação responsável

O teste usa uma partição isolada e estratificada; não há vazamento entre treino e teste. Ainda assim, o Bitext é um corpus em inglês e híbrido/sintético. Essas métricas não representam desempenho em reclamações brasileiras reais nem autorizam uso produtivo sem validação externa.
""",
        encoding="utf-8",
    )
    labels = sorted(test["intent"].unique())
    matrix = confusion_matrix(test["intent"], predictions, labels=labels)
    off_diagonal = []
    for actual_index, actual in enumerate(labels):
        for predicted_index, predicted in enumerate(labels):
            count = int(matrix[actual_index, predicted_index])
            if actual != predicted and count:
                off_diagonal.append((count, actual, predicted))
    off_diagonal.sort(reverse=True)
    per_intent = pd.DataFrame(report).T.drop(index=["accuracy", "macro avg", "weighted avg"], errors="ignore")
    lowest_f1 = per_intent.sort_values("f1-score").head(10)
    args.error_report.parent.mkdir(parents=True, exist_ok=True)
    confusion_lines = "\n".join(
        f"- `{actual}` → `{predicted}`: {count}" for count, actual, predicted in off_diagonal[:10]
    ) or "- Não houve confusões no conjunto de teste."
    f1_lines = "\n".join(
        f"- `{intent}`: F1 {row['f1-score']:.4f} ({int(row['support'])} exemplos)"
        for intent, row in lowest_f1.iterrows()
    )
    args.error_report.write_text(
        f"""# Análise de erros — baseline Bitext

## Pares mais confundidos

{confusion_lines}

## Dez intenções com menor F1 no teste

{f1_lines}

## Limite de interpretação

Esta análise mostra onde o baseline confunde rótulos dentro do próprio Bitext.
Ela não mede a qualidade em feedbacks reais brasileiros. A etapa de validação
humana em PT-BR é necessária antes de qualquer conclusão externa.
""", encoding="utf-8")
    plt.figure(figsize=(12, 10))
    plt.imshow(matrix, cmap="Blues")
    plt.colorbar(label="Registros")
    plt.title("Matriz de confusão — intenções Bitext (teste)")
    plt.xlabel("Predição")
    plt.ylabel("Rótulo real")
    plt.tight_layout()
    plt.savefig(args.report_md.parent / "01_matriz_confusao_intencoes.png", dpi=160)
    plt.close()
    print(f"Baseline salvo em: {args.model}")
    print(f"Macro F1: {results['macro_f1']:.4f}")


if __name__ == "__main__":
    main()
