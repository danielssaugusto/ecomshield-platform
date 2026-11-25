"""Train the TP4 intent classifier and persist all required evaluation evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline


def make_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            ("classifier", LogisticRegression(max_iter=1_500, class_weight="balanced", random_state=42)),
        ]
    )


def evaluate(model: Pipeline, text: pd.Series, labels: pd.Series) -> dict:
    predictions = model.predict(text)
    probabilities = model.predict_proba(text)
    classes = model.classes_
    precision, recall, f1, support = precision_recall_fscore_support(labels, predictions, labels=classes, zero_division=0)
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "roc_auc_ovr_macro": float(roc_auc_score(labels, probabilities, labels=classes, multi_class="ovr", average="macro")),
        "per_class": {
            label: {"precision": float(p), "recall": float(r), "f1": float(score), "support": int(count)}
            for label, p, r, score, count in zip(classes, precision, recall, f1, support)
        },
        "classification_report": classification_report(labels, predictions, output_dict=True, zero_division=0),
        "predictions": predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/bitext_retail_intents.parquet"))
    parser.add_argument("--model", type=Path, default=Path("models/bitext_intent_tfidf_logreg.joblib"))
    parser.add_argument("--metrics", type=Path, default=Path("data/processed/tp4_intent_evaluation.json"))
    parser.add_argument("--report", type=Path, default=Path("reports/tp4_intent_model/relatorio.md"))
    parser.add_argument("--matrix", type=Path, default=Path("reports/tp4_intent_model/matriz_confusao.png"))
    args = parser.parse_args()

    frame = pd.read_parquet(args.dataset)
    train = frame[frame["split"].isin(["train", "validation"])].copy()
    test = frame[frame["split"] == "test"].copy()
    pipeline = make_pipeline()
    parameters = {
        "tfidf__min_df": [1, 2, 3],
        "classifier__C": [0.5, 1.0, 2.0],
    }
    search = GridSearchCV(pipeline, parameters, scoring="f1_macro", cv=3, n_jobs=-1, refit=True)
    search.fit(train["text"], train["intent"])
    tuned = evaluate(search.best_estimator_, test["text"], test["intent"])

    dummy = Pipeline([("tfidf", TfidfVectorizer()), ("classifier", DummyClassifier(strategy="most_frequent"))])
    dummy.fit(train["text"], train["intent"])
    baseline_predictions = dummy.predict(test["text"])
    baseline = {
        "strategy": "most_frequent",
        "accuracy": float(accuracy_score(test["intent"], baseline_predictions)),
        "macro_f1": float(f1_score(test["intent"], baseline_predictions, average="macro", zero_division=0)),
    }
    result = {
        "dataset": "bitext-retail-ecommerce-intents-v1",
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "grid_search": {"cv": 3, "scoring": "f1_macro", "parameters": parameters, "best_params": search.best_params_, "best_cv_macro_f1": float(search.best_score_)},
        "baseline": baseline,
        "tuned_model": {key: value for key, value in tuned.items() if key != "predictions"},
        "gain_over_baseline_macro_f1": float(tuned["macro_f1"] - baseline["macro_f1"]),
        "limitation": "The Bitext corpus is English and hybrid/synthetic; these in-distribution metrics are not a PT-BR or production-performance claim.",
    }
    args.model.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(search.best_estimator_, args.model)
    args.metrics.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    labels = list(search.best_estimator_.classes_)
    matrix = confusion_matrix(test["intent"], tuned["predictions"], labels=labels)
    plt.figure(figsize=(18, 15))
    sns.heatmap(matrix, cmap="Blues", cbar=False, xticklabels=labels, yticklabels=labels)
    plt.title("Matriz de confusão - classificador ajustado")
    plt.xlabel("Predito")
    plt.ylabel("Real")
    plt.tight_layout()
    plt.savefig(args.matrix, dpi=180)
    plt.close()

    args.report.write_text(
        f"""# TP4 - Classificador de intenções\n\n"
        f"- Pipeline: TF-IDF (1-2 gramas) + LogisticRegression\n"
        f"- Dados: {len(train):,} treino/validação e {len(test):,} teste\n"
        f"- GridSearchCV: 3 folds, métrica macro F1\n"
        f"- Parâmetros pesquisados: `tfidf__min_df` = [1, 2, 3]; `classifier__C` = [0.5, 1.0, 2.0]\n"
        f"- Melhores parâmetros: `{search.best_params_}`\n"
        f"- Melhor macro F1 de validação cruzada: {search.best_score_:.4f}\n\n"
        f"## Teste isolado\n\n"
        f"| Modelo | Accuracy | Macro F1 | ROC-AUC OvR macro |\n| --- | ---: | ---: | ---: |\n"
        f"| Baseline (classe mais frequente) | {baseline['accuracy']:.4f} | {baseline['macro_f1']:.4f} | N/A |\n"
        f"| Modelo ajustado | {tuned['accuracy']:.4f} | {tuned['macro_f1']:.4f} | {tuned['roc_auc_ovr_macro']:.4f} |\n\n"
        f"O ganho de macro F1 sobre a baseline foi {tuned['macro_f1'] - baseline['macro_f1']:.4f}. A matriz de confusão está em `matriz_confusao.png`; as métricas por classe estão em `tp4_intent_evaluation.json`.\n\n"
        f"## Limitação\n\n{result['limitation']}\n""",
        encoding="utf-8",
    )
    print(f"Modelo salvo em {args.model}; Macro F1={tuned['macro_f1']:.4f}; ROC-AUC={tuned['roc_auc_ovr_macro']:.4f}")


if __name__ == "__main__":
    main()
