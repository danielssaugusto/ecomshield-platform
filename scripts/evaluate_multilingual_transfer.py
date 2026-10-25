"""Evaluate a predeclared cross-lingual Bitext model on held-out PT-BR reviews.

The 422 human-labeled reviews are loaded only after model selection on Bitext
validation. They never enter embedding fitting, classifier fitting, or tuning.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from evaluate_ptbr_external import sha256_file, summarize_predictions
from fastembed import TextEmbedding
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
BITEXT = ROOT / "data/processed/bitext_retail_intents.parquet"
PTBR = ROOT / "data/processed/ptbr_intent_validation_final.csv"
OUT_JSON = ROOT / "reports/tp3_data/transferencia_multilingue.json"
OUT_MD = ROOT / "reports/tp3_data/transferencia_multilingue.md"
CACHE = ROOT / ".cache/tp3-embeddings"
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SOURCE = "Qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q"
SOURCE_REVISION = "faf4aa4225822f3bc6376869cb1164e8e3feedd0"
TRAIN_PER_INTENT = 200
VALID_PER_INTENT = 50
SEED = 20261024
CS = (0.1, 1.0, 10.0)


def fixed_sample(frame: pd.DataFrame, n: int) -> pd.DataFrame:
    """Stable, label-stratified cap without inspecting Portuguese annotations."""
    return (
        frame.groupby("intent", group_keys=False)
        .sample(n=n, random_state=SEED)
        .sort_values("record_id")
        .reset_index(drop=True)
    )


def embedding_matrix(encoder: TextEmbedding, texts: pd.Series) -> np.ndarray:
    vectors = np.stack(list(encoder.embed(texts.tolist(), batch_size=64, parallel=None)))
    if vectors.shape != (len(texts), 384) or not np.isfinite(vectors).all():
        raise ValueError("Embeddings incompletos ou não finitos.")
    return vectors


def main() -> None:
    source = pd.read_parquet(BITEXT)
    required = {"record_id", "text", "intent", "split"}
    if required.difference(source.columns):
        raise ValueError("Bitext preparado não contém as colunas exigidas.")
    taxonomy = sorted(source["intent"].unique().tolist())
    if len(taxonomy) != 46:
        raise ValueError("Taxonomia Bitext deve ter 46 intenções.")
    train = fixed_sample(source[source["split"].eq("train")], TRAIN_PER_INTENT)
    valid = fixed_sample(source[source["split"].eq("validation")], VALID_PER_INTENT)
    if set(train["text"]) & set(valid["text"]):
        raise ValueError("Texto idêntico entre treino e validação Bitext.")

    encoder = TextEmbedding(model_name=MODEL, cache_dir=str(CACHE), threads=4)
    hub_cache = CACHE / f"models--{SOURCE.replace('/', '--')}"
    revision = (hub_cache / "refs/main").read_text(encoding="utf-8").strip()
    if revision != SOURCE_REVISION:
        raise ValueError("Revisão do encoder diferente da revisão pré-declarada.")
    model_file = hub_cache / "snapshots" / revision / "model_optimized.onnx"
    if not model_file.is_file():
        raise ValueError("Pesos ONNX da revisão declarada não foram encontrados.")
    x_train = embedding_matrix(encoder, train["text"])
    x_valid = embedding_matrix(encoder, valid["text"])
    y_train, y_valid = train["intent"].tolist(), valid["intent"].tolist()

    candidates = []
    for c in CS:
        classifier = LogisticRegression(C=c, max_iter=1000, random_state=SEED)
        classifier.fit(x_train, y_train)
        guess = classifier.predict(x_valid)
        candidates.append({
            "C": c,
            "macro_f1": float(f1_score(y_valid, guess, labels=taxonomy, average="macro")),
            "accuracy": float(accuracy_score(y_valid, guess)),
            "classifier": classifier,
        })
    selected = max(candidates, key=lambda row: (row["macro_f1"], -row["C"]))
    classifier = selected["classifier"]

    # The external annotations first enter memory after the model is fixed.
    external = pd.read_csv(PTBR, dtype=str, keep_default_na=False)
    eligible = external.loc[external["evaluation_eligible"].eq("True")].copy()
    if len(eligible) != 422 or not eligible["sample_id"].is_unique:
        raise ValueError("Teste PT-BR alterado: esperados 422 IDs únicos.")
    if set(train["text"]) & set(eligible["feedback_text"]):
        raise ValueError("Texto idêntico entre treino e teste externo.")
    x_external = embedding_matrix(encoder, eligible["feedback_text"])
    predicted = classifier.predict(x_external).tolist()
    actual = eligible["validated_intent"].tolist()
    result = summarize_predictions(actual, predicted, taxonomy)

    provenance = {
        "bitext_sha256": sha256_file(BITEXT),
        "ptbr_sha256": sha256_file(PTBR),
        "encoder_source": SOURCE,
        "encoder_revision": revision,
        "encoder_onnx_sha256": sha256_file(model_file),
        "seed": SEED,
        "train_per_intent": TRAIN_PER_INTENT,
        "validation_per_intent": VALID_PER_INTENT,
        "candidate_C": list(CS),
        "selected_C": selected["C"],
        "selection_metric": "Bitext validation macro-F1",
        "used_ptbr_for_training_or_selection": False,
    }
    payload = {
        "provenance": provenance,
        "bitext_validation": [
            {key: value for key, value in row.items() if key != "classifier"}
            for row in candidates
        ],
        "external": result,
        "predictions": [
            {"sample_id": sample_id, "actual": truth, "predicted": guess}
            for sample_id, truth, guess in zip(eligible["sample_id"], actual, predicted)
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    top_errors = result["error_pairs"][:10]
    error_rows = "\n".join(
        f"| `{row['actual']}` | `{row['predicted']}` | {row['count']} |" for row in top_errors
    )
    by_class = "\n".join(
        f"| `{name}` | {row['support']} | {row['recall']:.3f} | {row['f1']:.3f} |"
        for name, row in sorted(result["per_intent"].items(), key=lambda item: -item[1]["support"])
    )
    candidate_rows = "\n".join(
        f"| {row['C']} | {row['macro_f1']:.4f} | {row['accuracy']:.4f} |"
        for row in candidates
    )
    majority = Counter(actual).most_common(1)[0]
    OUT_MD.write_text(
        f"""# TP3 — teste de transferência multilíngue sem ajuste no PT-BR

Um encoder multilíngue congelado representa textos ingleses do Bitext e reviews
portugueses do B2W. A regressão logística foi treinada em {len(train)} textos
Bitext (200 por intenção). O único hiperparâmetro escolhido, `C`, foi selecionado
por Macro-F1 em {len(valid)} textos da validação Bitext (50 por intenção). Os 422
rótulos PT-BR foram lidos apenas após essa escolha. Não se usou tradução,
heurística de palavras-chave, nota B2W ou dados PT-BR para treino/seleção.

Modelo: `{MODEL}`; pesos ONNX da revisão `{revision}` (SHA-256:
`{provenance['encoder_onnx_sha256']}`). Semente: {SEED}.
SHA-256 Bitext: `{provenance['bitext_sha256']}`; PT-BR:
`{provenance['ptbr_sha256']}`.

## Seleção no Bitext

| C | Macro-F1 validação | Acurácia validação |
| ---: | ---: | ---: |
{candidate_rows}

Selecionado: `C={selected['C']}`. Esses números não são estimativas de
desempenho em português ou atendimento real.

## Teste externo PT-BR

| Medida | Resultado |
| --- | ---: |
| Casos elegíveis | {result['eligible_rows']} |
| Acertos | {result['correct_rows']} |
| Acurácia | {result['accuracy']:.4f} |
| Macro-F1 nas 14 classes com suporte | {result['macro_f1_supported']:.4f} |
| Previsão constante da classe majoritária, comparação descritiva | {majority[1] / len(actual):.4f} |
| Previsões fora das 14 classes com suporte | {result['predictions_for_unsupported_intents']} |

### Por intenção real

| Intenção | Suporte | Recall | F1 |
| --- | ---: | ---: | ---: |
{by_class}

### Erros frequentes

| Rótulo humano | Previsão | Casos |
| --- | --- | ---: |
{error_rows}

## Interpretação

O teste separa parcialmente lacuna de idioma de lacuna de tarefa. O encoder
alinha idiomas, mas o Bitext rotula pedidos de ajuda ao atendimento. Exemplo:
`submit_product_feedback` no Bitext é a intenção de **enviar** uma avaliação;
um review B2W é a avaliação já **escrita**. Nenhum encoder resolve essa diferença
de definição sozinho. A amostra B2W foi estratificada por estrelas, e 292 de 422
casos têm o mesmo rótulo; por isso acurácia isolada é enganosa. Não há estimativa
para as 32 intenções ausentes. O [JSON](transferencia_multilingue.json) contém
predições por ID pseudônimo, sem texto bruto.

Como o mesmo teste externo já foi consultado em uma avaliação anterior, este
novo resultado é análise exploratória de transferência, **não** uma segunda
confirmação independente de desempenho. Para atingir uma meta de 60% de modo
crível em solicitações reais, é necessário coletar dados PT-BR de suporte,
definir rótulos coerentes e reservar uma nova avaliação humana cega.
""",
        encoding="utf-8",
    )
    print(f"Bitext validation C={selected['C']}: Macro-F1={selected['macro_f1']:.4f}")
    print(f"PT-BR: {result['correct_rows']}/{result['eligible_rows']} = {result['accuracy']:.4f}; Macro-F1={result['macro_f1_supported']:.4f}")


if __name__ == "__main__":
    main()
