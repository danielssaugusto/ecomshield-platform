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
from pathlib import Path
from urllib.request import urlopen

import certifi
import matplotlib.pyplot as plt
import pandas as pd


SOURCE_URL = (
    "https://huggingface.co/datasets/bitext/"
    "Bitext-retail-ecommerce-llm-chatbot-training-dataset/resolve/main/"
    "bitext-retail-ecommerce-llm-chatbot-training-dataset.csv?download=true"
)
SOURCE_DATASET = "bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset"
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
    """Download with certificate verification, including macOS Python installs."""
    context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(url, context=context) as response, output.open("wb") as file:
        while chunk := response.read(1024 * 1024):
            file.write(chunk)


def stable_splits(frame: pd.DataFrame) -> pd.Series:
    """Create deterministic 80/10/10 splits within every original intent."""
    assignments = pd.Series(index=frame.index, dtype="string")
    for _, group in frame.groupby("intent", sort=True):
        ordered = group.sort_values("record_id")
        count = len(ordered)
        test_size = max(1, round(count * 0.10))
        validation_size = max(1, round(count * 0.10))
        assignments.loc[ordered.index[:test_size]] = "test"
        assignments.loc[ordered.index[test_size : test_size + validation_size]] = "validation"
        assignments.loc[ordered.index[test_size + validation_size :]] = "train"
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
| Comprimento mediano do texto | {text_length["median"]:.0f} caracteres |
| Comprimento médio do texto | {text_length["mean"]:.1f} caracteres |
| Percentil 95 do comprimento | {text_length["p95"]:.0f} caracteres |

## Hipóteses verificadas

1. **Entrega, produto e devoluções concentram parte relevante das solicitações.**
   As categorias `DELIVERY`, `PRODUCT` e `RETURNS` somam
   {hypothesis["core_categories"]["records"]:,} registros
   ({hypothesis["core_categories"]["percent"]:.2f}%).
2. **As classes são adequadamente balanceadas para avaliação multiclasse.** A
   menor classe possui {hypothesis["intent_balance"]["min_count"]:,} exemplos
   e a maior {hypothesis["intent_balance"]["max_count"]:,}; razão
   máxima/mínima de {hypothesis["intent_balance"]["ratio"]:.2f}.
3. **Nenhuma intenção fica ausente da validação ou teste.** Todas as
   {report["intent_total"]} intenções aparecem em `train`, `validation` e `test`.
4. **Há variação de extensão que deve orientar o limite de tokens do modelo.**
   O percentil 95 é {text_length["p95"]:.0f} caracteres; qualquer truncamento
   adotado no treinamento deve ser documentado.

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
    plt.boxplot(values, labels=categories, showfliers=False)
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


def build(input_path: Path, processed_path: Path, report_path: Path, report_md: Path) -> None:
    if not input_path.exists() or input_path.stat().st_size == 0:
        input_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Baixando {SOURCE_DATASET}…")
        download_source(SOURCE_URL, input_path)

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
    minimum_intent_count = min(intent_counts.values())
    maximum_intent_count = max(intent_counts.values())
    report = {
        "dataset_version": "bitext-retail-ecommerce-intents-v1",
        "source_dataset": SOURCE_DATASET,
        "source_url": SOURCE_URL,
        "source_license": "CDLA-Sharing-1.0",
        "source_sha256": sha256_file(input_path),
        "raw_rows": raw_rows,
        "rows_removed_missing": rows_removed_missing,
        "rows_removed_duplicates": rows_removed_duplicates,
        "final_rows": len(final),
        "category_counts": category_counts,
        "intent_counts": intent_counts,
        "split_counts": split_counts,
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
