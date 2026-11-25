#!/usr/bin/env python3
"""Build the reproducible Bitext intent-classification dataset.

The source labels are preserved exactly as published.  This script never
infers or rewrites an intent from keywords, ratings, or model output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import tempfile
from pathlib import Path
from urllib.request import urlopen

import certifi
import matplotlib.pyplot as plt
import pandas as pd


SOURCE_URL = (
    "https://huggingface.co/datasets/bitext/"
    "Bitext-retail-ecommerce-llm-chatbot-training-dataset/resolve/"
    "12dd624ddcd3057382b2faad661bcda1fa869491/"
    "bitext-retail-ecommerce-llm-chatbot-training-dataset.csv?download=true"
)
SOURCE_DATASET = "bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset"
SOURCE_SHA256 = "13a988266fed4e2b2c1ff947a89ef220ce09b5b13ac83c4a1496c0d7b81e8127"
REQUIRED_COLUMNS = {"instruction", "intent", "category", "tags", "response"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_text(value: object) -> str:
    """Normalize whitespace only; preserve the source's semantic content."""
    return " ".join(str(value).split())


def download_source(url: str, output: Path) -> None:
    """Download atomically with certificate verification."""
    context = ssl.create_default_context(cafile=certifi.where())
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".bitext-", suffix=".part", delete=False) as file:
            temporary_path = Path(file.name)
            with urlopen(url, context=context, timeout=60) as response:
                while chunk := response.read(1024 * 1024):
                    file.write(chunk)
        if sha256_file(temporary_path) != SOURCE_SHA256:
            raise ValueError("O Bitext baixado não corresponde ao SHA-256 fixado.")
        temporary_path.replace(output)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def stable_splits(frame: pd.DataFrame) -> pd.Series:
    """Split by intent while keeping every repeated text in one partition."""
    assignments = pd.Series(index=frame.index, dtype="string")
    if frame.groupby("text")["intent"].nunique().gt(1).any():
        raise ValueError("Há textos idênticos com intenções diferentes; revise os rótulos antes da divisão.")
    for _, intent_rows in frame.groupby("intent", sort=True):
        text_groups = sorted(
            (group for _, group in intent_rows.groupby("text", sort=False)),
            key=lambda group: group["record_id"].min(),
        )
        target_test = max(1, round(len(intent_rows) * 0.10))
        target_validation = max(1, round(len(intent_rows) * 0.10))
        test_rows = validation_rows = 0
        for group in text_groups:
            if test_rows < target_test:
                split = "test"
                test_rows += len(group)
            elif validation_rows < target_validation:
                split = "validation"
                validation_rows += len(group)
            else:
                split = "train"
            assignments.loc[group.index] = split
    return assignments


def write_markdown_report(report: dict[str, object], output: Path) -> None:
    categories = report["category_counts"]
    intents = report["intent_counts"]
    splits = report["split_counts"]
    category_rows = "\n".join(f"| `{name}` | {count:,} |" for name, count in categories.items())
    intent_rows = "\n".join(f"| `{name}` | {count:,} |" for name, count in intents.items())
    split_rows = "\n".join(f"| `{name}` | {count:,} |" for name, count in splits.items())
    text_length = report["text_length_chars"]
    hypothesis = report["hypotheses"]
    output.write_text(
        f"""# Relatório de dados — Bitext Retail eCommerce

## Finalidade

Este é o corpus rotulado usado para a tarefa de classificação de intenção.
Os campos `category` e `intent` são os rótulos publicados pela fonte; o
E-ComShield não cria rótulos por palavras-chave, nota ou heurística.

## Rastreabilidade

- Fonte: [`{SOURCE_DATASET}`](https://huggingface.co/datasets/bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset)
- Licença da fonte: CDLA-Sharing-1.0
- SHA-256 do CSV baixado: `{report["source_sha256"]}`
- Linhas no CSV de origem: {report["raw_rows"]:,}
- Linhas removidas por texto/rótulo ausente: {report["rows_removed_missing"]:,}
- Duplicatas exatas removidas: {report["rows_removed_duplicates"]:,}
- Linhas finais: {report["final_rows"]:,}

> Limitação conhecida: o Bitext se descreve como um dataset híbrido sintético.
> Ele é usado aqui porque fornece a variável-alvo de intenção já definida pela
> fonte. O B2W-Reviews01 continua separado, apenas para EDA e análise de
> feedback real em português.

## Esquema final

| Campo | Descrição |
| --- | --- |
| `text` | Solicitação do cliente (`instruction` da fonte) |
| `category` | Categoria original do Bitext |
| `intent` | Intenção original do Bitext, variável-alvo |
| `response` | Resposta de referência da fonte; não usada como entrada do classificador |
| `tags` | Variações linguísticas indicadas pela fonte |
| `split` | Partição estratificada e determinística (80/10/10) |

## Integridade e inspeção estrutural

| Verificação | Resultado |
| --- | ---: |
| Valores ausentes nos campos de treino (`text`, `category`, `intent`) | 0 |
| Duplicatas exatas no dataset final | 0 |
| Textos idênticos em partições diferentes | {report["cross_split_duplicate_texts"]} |
| Comprimento mediano do texto | {text_length["median"]:.0f} caracteres |
| Comprimento médio do texto | {text_length["mean"]:.1f} caracteres |
| Percentil 95 do comprimento | {text_length["p95"]:.0f} caracteres |

## Hipóteses verificadas

1. **Entrega, produto e devoluções concentram parte relevante das solicitações.**
   As categorias `DELIVERY`, `PRODUCT` e `RETURNS` somam
   {hypothesis["core_categories"]["records"]:,} registros
   ({hypothesis["core_categories"]["percent"]:.2f}%).
2. **Solicitações de devolução são mais frequentes do que feedback de produto.**
   `RETURNS` tem {hypothesis["returns_vs_feedback"]["returns"]:,} registros,
   contra {hypothesis["returns_vs_feedback"]["feedback"]:,} em `FEEDBACK`
   (razão {hypothesis["returns_vs_feedback"]["ratio"]:.2f}).
3. **Problemas, prazo e rastreamento concentram intenções de entrega.**
   `delivery_issue`, `delivery_time` e `track_delivery` somam
   {hypothesis["delivery_issue_time_tracking"]["records"]:,} registros,
   {hypothesis["delivery_issue_time_tracking"]["percent_of_delivery"]:.2f}%
   da categoria `DELIVERY`.

As classes têm entre {hypothesis["intent_balance"]["min_count"]:,} e
{hypothesis["intent_balance"]["max_count"]:,} exemplos. Todas as
{report["intent_total"]} intenções aparecem em `train`, `validation` e `test`.
O percentil 95 de extensão é {text_length["p95"]:.0f} caracteres; qualquer
truncamento no treinamento deve ser documentado.

## Categorias

| Categoria | Registros |
| --- | ---: |
{category_rows}

## Intenções

| Intenção | Registros |
| --- | ---: |
{intent_rows}

## Partições

| Partição | Registros |
| --- | ---: |
{split_rows}

## Figuras geradas

- `01_distribuicao_categorias.png`
- `02_distribuicao_intencoes.png`
- `03_comprimento_textos_por_categoria.png`
- `04_particoes_por_categoria.png`
- `05_histograma_comprimento_textos.png`
""",
        encoding="utf-8",
    )


def create_eda_figures(final: pd.DataFrame, report_dir: Path) -> None:
    """Write EDA figures from the processed source-labeled corpus."""
    report_dir.mkdir(parents=True, exist_ok=True)

    category_counts = final["category"].value_counts().sort_values()
    plt.figure(figsize=(10, 5))
    category_counts.plot.barh(color="#0f766e")
    plt.xlabel("Registros")
    plt.ylabel("Categoria original")
    plt.title("Bitext Retail eCommerce — distribuição por categoria")
    plt.tight_layout()
    plt.savefig(report_dir / "01_distribuicao_categorias.png", dpi=160)
    plt.close()

    intent_counts = final["intent"].value_counts().sort_values()
    plt.figure(figsize=(10, 12))
    intent_counts.plot.barh(color="#2563eb")
    plt.xlabel("Registros")
    plt.ylabel("Intenção original")
    plt.title("Bitext Retail eCommerce — distribuição por intenção")
    plt.tight_layout()
    plt.savefig(report_dir / "02_distribuicao_intencoes.png", dpi=160)
    plt.close()

    lengths = final.assign(text_length_chars=final["text"].str.len())
    categories = sorted(lengths["category"].unique())
    values = [lengths.loc[lengths["category"] == category, "text_length_chars"] for category in categories]
    plt.figure(figsize=(12, 6))
    plt.boxplot(values, tick_labels=categories, showfliers=False)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Caracteres no texto")
    plt.title("Comprimento do texto por categoria")
    plt.tight_layout()
    plt.savefig(report_dir / "03_comprimento_textos_por_categoria.png", dpi=160)
    plt.close()

    split_by_category = pd.crosstab(final["category"], final["split"])
    split_by_category = split_by_category.reindex(columns=["train", "validation", "test"])
    split_by_category.plot(
        kind="bar", stacked=True, figsize=(12, 6), color=["#0f766e", "#f59e0b", "#2563eb"]
    )
    plt.xlabel("Categoria original")
    plt.ylabel("Registros")
    plt.title("Partições estratificadas por categoria")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Split")
    plt.tight_layout()
    plt.savefig(report_dir / "04_particoes_por_categoria.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    lengths["text_length_chars"].clip(upper=1000).plot.hist(bins=40, color="#ea580c")
    plt.xlabel("Caracteres no texto (valores acima de 1.000 agrupados)")
    plt.ylabel("Solicitações")
    plt.title("Distribuição do comprimento das solicitações")
    plt.tight_layout()
    plt.savefig(report_dir / "05_histograma_comprimento_textos.png", dpi=160)
    plt.close()


def build(input_path: Path, processed_path: Path, report_path: Path, report_md: Path) -> None:
    if not input_path.exists() or input_path.stat().st_size == 0:
        input_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Baixando {SOURCE_DATASET}…")
        download_source(SOURCE_URL, input_path)

    source_hash = sha256_file(input_path)
    if source_hash != SOURCE_SHA256:
        raise ValueError(f"Bitext SHA-256 inesperado em {input_path}: {source_hash}")

    raw = pd.read_csv(input_path, dtype="string", keep_default_na=False)
    missing_columns = REQUIRED_COLUMNS.difference(raw.columns)
    if missing_columns:
        raise ValueError(f"CSV sem as colunas obrigatórias: {sorted(missing_columns)}")

    frame = raw.loc[:, ["instruction", "category", "intent", "tags", "response"]].copy()
    frame = frame.rename(columns={"instruction": "text"})
    for column in frame.columns:
        frame[column] = frame[column].map(clean_text)

    raw_rows = len(frame)
    complete = frame[frame[["text", "category", "intent"]].ne("").all(axis=1)].copy()
    rows_removed_missing = raw_rows - len(complete)
    deduplicated = complete.drop_duplicates(subset=["text", "category", "intent", "response"]).copy()
    rows_removed_duplicates = len(complete) - len(deduplicated)

    deduplicated["record_id"] = deduplicated.apply(
        lambda row: hashlib.sha256(
            f"{row['text']}\x1f{row['category']}\x1f{row['intent']}\x1f{row['response']}".encode("utf-8")
        ).hexdigest(),
        axis=1,
    )
    deduplicated["source_dataset"] = SOURCE_DATASET
    deduplicated["split"] = stable_splits(deduplicated)
    if deduplicated.groupby("text")["split"].nunique().gt(1).any():
        raise AssertionError("A divisão colocou textos idênticos em partições diferentes.")
    final = deduplicated[
        ["record_id", "source_dataset", "text", "category", "intent", "tags", "response", "split"]
    ].sort_values(["split", "intent", "record_id"])

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    final.to_parquet(processed_path, index=False)

    category_counts = final["category"].value_counts().sort_index().to_dict()
    intent_counts = final["intent"].value_counts().sort_index().to_dict()
    split_counts = final["split"].value_counts().reindex(["train", "validation", "test"]).to_dict()
    text_lengths = final["text"].str.len()
    core_categories = final[final["category"].isin(["DELIVERY", "PRODUCT", "RETURNS"])]
    returns_count = category_counts["RETURNS"]
    feedback_count = category_counts["FEEDBACK"]
    delivery_focus_count = sum(
        intent_counts[name] for name in ["delivery_issue", "delivery_time", "track_delivery"]
    )
    minimum_intent_count = min(intent_counts.values())
    maximum_intent_count = max(intent_counts.values())
    report = {
        "dataset_version": "bitext-retail-ecommerce-intents-v1",
        "source_dataset": SOURCE_DATASET,
        "source_url": SOURCE_URL,
        "source_license": "CDLA-Sharing-1.0",
        "source_sha256": source_hash,
        "raw_rows": raw_rows,
        "rows_removed_missing": rows_removed_missing,
        "rows_removed_duplicates": rows_removed_duplicates,
        "final_rows": len(final),
        "category_counts": category_counts,
        "intent_counts": intent_counts,
        "split_counts": split_counts,
        "cross_split_duplicate_texts": int(final.groupby("text")["split"].nunique().gt(1).sum()),
        "intent_total": len(intent_counts),
        "text_length_chars": {
            "min": int(text_lengths.min()),
            "median": float(text_lengths.median()),
            "mean": float(text_lengths.mean()),
            "p95": float(text_lengths.quantile(0.95)),
            "max": int(text_lengths.max()),
        },
        "hypotheses": {
            "core_categories": {
                "records": len(core_categories),
                "percent": len(core_categories) / len(final) * 100,
            },
            "returns_vs_feedback": {
                "returns": returns_count,
                "feedback": feedback_count,
                "ratio": returns_count / feedback_count,
            },
            "delivery_issue_time_tracking": {
                "records": delivery_focus_count,
                "percent_of_delivery": delivery_focus_count / category_counts["DELIVERY"] * 100,
            },
            "intent_balance": {
                "min_count": minimum_intent_count,
                "max_count": maximum_intent_count,
                "ratio": maximum_intent_count / minimum_intent_count,
            },
        },
        "labeling_policy": "Original Bitext category and intent labels preserved without relabeling.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown_report(report, report_md)

    create_eda_figures(final, report_md.parent)

    print(f"Dataset processado: {processed_path} ({len(final):,} registros)")
    print(f"Relatório: {report_md}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/bitext-retail-ecommerce/bitext-retail-ecommerce.csv"),
        help="CSV original. É baixado se ainda não existir.",
    )
    parser.add_argument(
        "--processed",
        type=Path,
        default=Path("data/processed/bitext_retail_intents.parquet"),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path("data/processed/bitext_retail_intents_report.json"),
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=Path("reports/bitext_retail_intents/relatorio.md"),
    )
    args = parser.parse_args()
    build(args.input, args.processed, args.report_json, args.report_md)


if __name__ == "__main__":
    main()
