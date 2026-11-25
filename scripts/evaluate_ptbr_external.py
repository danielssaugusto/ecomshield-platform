"""Evaluate the frozen Bitext baseline once on human-labeled B2W feedback.

This script never fits or adjusts the model. The 422 eligible Portuguese texts
remain an external test set, separate from the English Bitext training corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_predictions(actual: list[str], predicted: list[str], taxonomy: list[str]) -> dict:
    """Report metrics only for classes observed in the external ground truth."""
    if len(actual) != len(predicted) or not actual:
        raise ValueError("Rótulos reais e previstos precisam ter o mesmo tamanho não vazio.")
    if set(actual).difference(taxonomy) or set(predicted).difference(taxonomy):
        raise ValueError("Há intenções fora da taxonomia fixada.")
    support_counts = Counter(actual)
    supported = sorted(support_counts)
    predicted_counts = Counter(predicted)
    correct_counts = Counter(truth for truth, guess in zip(actual, predicted) if truth == guess)
    per_intent = {}
    for label in supported:
        true_positive = correct_counts[label]
        precision = true_positive / predicted_counts[label] if predicted_counts[label] else 0.0
        recall = true_positive / support_counts[label]
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_intent[label] = {
            "support": support_counts[label],
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    most_common, majority_count = support_counts.most_common(1)[0]
    errors = Counter((truth, guess) for truth, guess in zip(actual, predicted) if truth != guess)
    return {
        "eligible_rows": len(actual),
        "correct_rows": sum(truth == guess for truth, guess in zip(actual, predicted)),
        "supported_intents": len(supported),
        "unsupported_intents": sorted(set(taxonomy).difference(supported)),
        "accuracy": sum(truth == guess for truth, guess in zip(actual, predicted)) / len(actual),
        "majority_baseline_intent": most_common,
        "majority_baseline_accuracy": majority_count / len(actual),
        "macro_f1_supported": sum(row["f1"] for row in per_intent.values()) / len(supported),
        "weighted_f1_supported": sum(
            row["f1"] * row["support"] for row in per_intent.values()
        ) / len(actual),
        "per_intent": per_intent,
        "predicted_intent_counts": dict(sorted(predicted_counts.items())),
        "predictions_for_unsupported_intents": sum(
            guess not in support_counts for guess in predicted
        ),
        "error_pairs": [
            {"actual": truth, "predicted": guess, "count": count}
            for (truth, guess), count in sorted(
                errors.items(), key=lambda item: (-item[1], item[0])
            )
        ],
    }


def subgroup_accuracy(actual: list[str], predicted: list[str], groups: list[str]) -> dict[str, dict]:
    """Descriptive accuracy by a pre-existing annotation-quality group."""
    if len(actual) != len(predicted) or len(actual) != len(groups):
        raise ValueError("Rótulos, previsões e grupos precisam ter o mesmo tamanho.")
    counts: dict[str, dict] = {}
    for truth, guess, group in zip(actual, predicted, groups):
        row = counts.setdefault(group, {"rows": 0, "correct": 0})
        row["rows"] += 1
        row["correct"] += truth == guess
    return {
        group: {**row, "accuracy": row["correct"] / row["rows"]}
        for group, row in sorted(counts.items())
    }


def render_markdown(summary: dict, provenance: dict, diagnostics: dict, example_errors: list[dict]) -> str:
    rows = [
        f"| `{label}` | {values['support']} | {values['precision']:.3f} | "
        f"{values['recall']:.3f} | {values['f1']:.3f} |"
        for label, values in sorted(
            summary["per_intent"].items(),
            key=lambda item: (-item[1]["support"], item[0]),
        )
    ]
    pairs = [
        f"| `{item['actual']}` | `{item['predicted']}` | {item['count']} |"
        for item in summary["error_pairs"][:10]
    ]
    cases = [
        f"| `{item['sample_id']}` | `{item['actual']}` | `{item['predicted']}` |"
        for item in example_errors
    ]
    return f"""# TP3 — avaliação externa PT-BR do baseline congelado

## Protocolo e proveniência

O modelo TF-IDF (uni e bigramas) + regressão logística foi treinado somente na
partição `train` do Bitext, em inglês. Seu código e artefato foram congelados
antes desta avaliação. Nenhum dos 500 feedbacks B2W anotados foi usado para
ajustar o vocabulário, o modelo, hiperparâmetros ou limiares. A avaliação
principal exclui os 78 registros marcados incertos por qualquer anotador.

- CSV validado (SHA-256): `{provenance['external_dataset_sha256']}`.
- Modelo avaliado (SHA-256): `{provenance['model_sha256']}`.
- Receita de treinamento (SHA-256): `{provenance['training_script_sha256']}`.
- Textos idênticos entre Bitext treino e B2W elegível: {provenance['identical_train_external_texts']}.
- Registros com vetor TF-IDF vazio: {provenance['empty_feature_vectors']} de {summary['eligible_rows']}.
- Acertos com vetor vazio: {provenance['correct_empty_vectors']}; acertos com vetor não vazio: {provenance['correct_nonempty_vectors']}.

## Resultados

| Medida | Resultado |
| --- | ---: |
| Feedbacks elegíveis | {summary['eligible_rows']} |
| Acertos | {summary['correct_rows']} |
| Intenções com suporte | {summary['supported_intents']} de {provenance['taxonomy_size']} |
| Acurácia do modelo | {summary['accuracy']:.4f} |
| Acurácia de prever sempre `{summary['majority_baseline_intent']}` | {summary['majority_baseline_accuracy']:.4f} |
| Macro-F1 nas intenções com suporte | {summary['macro_f1_supported']:.4f} |
| Weighted-F1 nas intenções com suporte | {summary['weighted_f1_supported']:.4f} |

A linha de base majoritária usa apenas a distribuição dos rótulos para comparação
descritiva. Não é um classificador treinado com esses feedbacks. O Macro-F1 é
calculado nas {summary['supported_intents']} intenções com pelo menos um rótulo real;
as outras {len(summary['unsupported_intents'])} não têm estimativa de desempenho.
Predições para intenções sem suporte no conjunto: {summary['predictions_for_unsupported_intents']}.

### Diagnóstico de cobertura textual e revisão humana

| Subconjunto | Casos | Acertos | Acurácia |
| --- | ---: | ---: | ---: |
| Vetor TF-IDF vazio | {diagnostics['empty_vectors']['rows']} | {diagnostics['empty_vectors']['correct']} | {diagnostics['empty_vectors']['accuracy']:.4f} |
| Vetor TF-IDF não vazio | {diagnostics['nonempty_vectors']['rows']} | {diagnostics['nonempty_vectors']['correct']} | {diagnostics['nonempty_vectors']['accuracy']:.4f} |
| Dupla concordância humana | {diagnostics['validation_method']['double_agreement']['rows']} | {diagnostics['validation_method']['double_agreement']['correct']} | {diagnostics['validation_method']['double_agreement']['accuracy']:.4f} |
| Adjudicação humana | {diagnostics['validation_method']['human_adjudication']['rows']} | {diagnostics['validation_method']['human_adjudication']['correct']} | {diagnostics['validation_method']['human_adjudication']['accuracy']:.4f} |

Esses estratos são diagnósticos descritivos, não testes independentes nem
estimativas de desempenho em produção. A diferença entre grupos de anotação
não mede qualidade dos revisores, porque os casos adjudicados tendem a ser
mais ambíguos.

### Métricas por intenção

| Intenção real | Suporte | Precisão | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

### Erros mais frequentes

| Intenção real | Previsão | Casos |
| --- | --- | ---: |
{chr(10).join(pairs) if pairs else '| — | — | 0 |'}

Casos concretos para conferência no CSV local, sem publicar o texto do cliente:

| ID opaco | Intenção humana | Previsão |
| --- | --- | --- |
{chr(10).join(cases) if cases else '| — | — | — |'}

## Interpretação e limites

O teste interno do Bitext não pode ser extrapolado para esta amostra: o corpus
de treino é inglês e híbrido/sintético, enquanto o B2W contém avaliações reais
de produtos em português, não chamados de suporte. A taxonomia de intenção foi
aplicada por anotadores humanos, mas pode não representar bem cada avaliação.
Todos os {provenance['empty_feature_vectors']} textos sem atributos reconhecidos
receberam a previsão `{provenance['empty_vector_prediction']}`; nenhum foi
classificado corretamente. Esse padrão é compatível com a lacuna de vocabulário
entre os dois idiomas, mas não isola todas as causas dos erros.
Os 500 rótulos cobrem 20 intenções; os {summary['eligible_rows']} elegíveis cobrem
somente {summary['supported_intents']}. A classe majoritária responde por
{summary['per_intent'][summary['majority_baseline_intent']]['support']} casos.
Classes com suporte 1–5 produzem estimativas especialmente instáveis. A amostra
foi estratificada por nota de avaliação e não estima prevalência em produção.
Entre as adjudicações, 84 decisões não têm justificativa textual recuperável,
incluindo 60 no subconjunto elegível. Não inventamos essas justificativas.

Este resultado mede apenas transferência para a amostra anotada. Não autoriza
integração do classificador à API ou alegação de desempenho em atendimento real.
O [JSON de resultados](avaliacao_externa_ptbr.json) inclui os 422 pares de
rótulo humano e previsão com ID pseudônimo e tamanho do vetor, sem texto bruto,
permitindo recalcular as métricas e conferir os exemplos acima.
Para ampliar a cobertura, será necessária nova revisão humana de solicitações
reais de suporte; acrescentar apenas reviews B2W pode manter o mesmo viés.
"""


def main() -> None:
    import joblib

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/ptbr_intent_validation_final.csv"))
    parser.add_argument("--manifest", type=Path, default=Path("data/annotations/ptbr_human_labels.manifest.json"))
    parser.add_argument("--bitext", type=Path, default=Path("data/processed/bitext_retail_intents.parquet"))
    parser.add_argument("--model", type=Path, default=Path("models/bitext_intent_tfidf_logreg.joblib"))
    parser.add_argument("--training-script", type=Path, default=Path("scripts/train_bitext_intent_baseline.py"))
    parser.add_argument("--output-json", type=Path, default=Path("reports/tp3_data/avaliacao_externa_ptbr.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/tp3_data/avaliacao_externa_ptbr.md"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if sha256_file(args.dataset) != manifest["final_csv_sha256"]:
        raise ValueError("O CSV PT-BR não corresponde às decisões humanas fixadas.")
    frame = pd.read_csv(args.dataset, dtype={"sample_id": str})
    required = {"sample_id", "feedback_text", "validated_intent", "evaluation_eligible"}
    if required.difference(frame.columns) or len(frame) != manifest["rows"] or not frame["sample_id"].is_unique:
        raise ValueError("O CSV PT-BR não tem a estrutura validada esperada.")
    eligible = frame.loc[frame["evaluation_eligible"].eq(True)].copy()
    if len(eligible) != 422 or eligible["feedback_text"].isna().any():
        raise ValueError("A amostra elegível difere das 422 observações revisadas.")
    bitext = pd.read_parquet(args.bitext, columns=["text", "intent", "split"])
    taxonomy = sorted(bitext["intent"].unique().tolist())
    if len(taxonomy) != 46:
        raise ValueError("A taxonomia Bitext esperada tem 46 intenções.")
    model = joblib.load(args.model)
    actual = eligible["validated_intent"].astype(str).tolist()
    predicted = model.predict(eligible["feedback_text"].astype(str)).tolist()
    summary = summarize_predictions(actual, predicted, taxonomy)
    vectors = model.named_steps["tfidf"].transform(eligible["feedback_text"].astype(str))
    empty_vectors = vectors.getnnz(axis=1) == 0
    empty_predictions = Counter(guess for guess, empty in zip(predicted, empty_vectors) if empty)
    train_texts = set(bitext.loc[bitext["split"].eq("train"), "text"])
    provenance = {
        "external_dataset_sha256": sha256_file(args.dataset),
        "bitext_dataset_sha256": sha256_file(args.bitext),
        "model_sha256": sha256_file(args.model),
        "training_script_sha256": sha256_file(args.training_script),
        "taxonomy_size": len(taxonomy),
        "identical_train_external_texts": len(train_texts.intersection(eligible["feedback_text"])),
        "empty_feature_vectors": int(empty_vectors.sum()),
        "correct_empty_vectors": int(sum(
            truth == guess and empty
            for truth, guess, empty in zip(actual, predicted, empty_vectors)
        )),
        "correct_nonempty_vectors": int(sum(
            truth == guess and not empty
            for truth, guess, empty in zip(actual, predicted, empty_vectors)
        )),
        "empty_vector_prediction": empty_predictions.most_common(1)[0][0] if empty_predictions else "n/a",
        "empty_vector_prediction_counts": dict(sorted(empty_predictions.items())),
    }
    if provenance["identical_train_external_texts"]:
        raise ValueError("Há textos idênticos entre treino e avaliação externa.")
    vector_groups = ["empty" if empty else "nonempty" for empty in empty_vectors]
    vector_accuracy = subgroup_accuracy(actual, predicted, vector_groups)
    validation_groups = eligible["validation_method"].astype(str).tolist()
    validation_accuracy = subgroup_accuracy(actual, predicted, validation_groups)
    if set(validation_accuracy) != {"double_agreement", "human_adjudication"}:
        raise ValueError("Métodos de validação humana inesperados na amostra elegível.")
    diagnostics = {
        "empty_vectors": vector_accuracy["empty"],
        "nonempty_vectors": vector_accuracy["nonempty"],
        "validation_method": validation_accuracy,
    }
    examples_by_pair = {}
    for row, truth, guess in zip(eligible.itertuples(index=False), actual, predicted):
        if truth != guess:
            examples_by_pair.setdefault(
                (truth, guess),
                {"sample_id": row.sample_id, "actual": truth, "predicted": guess},
            )
    examples = [
        examples_by_pair[(item["actual"], item["predicted"])]
        for item in summary["error_pairs"][:10]
    ]
    records = [
        {
            "sample_id": row.sample_id,
            "actual": truth,
            "predicted": guess,
            "validation_method": row.validation_method,
            "recognized_features": int(feature_count),
        }
        for row, truth, guess, feature_count in zip(
            eligible.itertuples(index=False), actual, predicted, vectors.getnnz(axis=1)
        )
    ]
    output = {
        "provenance": provenance,
        "summary": summary,
        "diagnostics": diagnostics,
        "error_example_ids": examples,
        "records": records,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(summary, provenance, diagnostics, examples), encoding="utf-8")
    print(f"Avaliação externa: {summary['eligible_rows']} casos, acurácia {summary['accuracy']:.4f}, Macro-F1 {summary['macro_f1_supported']:.4f}")


if __name__ == "__main__":
    main()
