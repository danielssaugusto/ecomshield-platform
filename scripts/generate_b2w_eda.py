#!/usr/bin/env python3
"""Generate reproducible exploratory analysis artifacts for B2W intent labels."""

from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


REQUIRED_COLUMNS = {
    "submission_date", "text", "intent", "intent_matches", "label_source", "overall_rating", "sentiment", "sentiment_source",
}
PALETTE = {"keyword_heuristic_v4": "#1D4ED8", "generic_topic_fallback_v1": "#F59E0B"}


def save_figure(output_dir: Path, filename: str) -> None:
    plt.tight_layout()
    plt.savefig(output_dir / filename, dpi=180, bbox_inches="tight")
    plt.close()


def load_dataset(path: Path) -> pd.DataFrame:
    data = pd.read_parquet(path)
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")
    if data.empty:
        raise ValueError("O dataset não contém registros.")
    data = data.copy()
    data["submission_date"] = pd.to_datetime(data["submission_date"], errors="coerce")
    data["text_length"] = data["text"].str.len()
    data["word_count"] = data["text"].str.split().str.len()
    return data


def plot_label_coverage(data: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    summary = data["label_source"].value_counts().rename_axis("origem").reset_index(name="registros")
    summary["percentual"] = summary["registros"] / len(data) * 100
    plt.figure(figsize=(8, 5))
    axis = sns.barplot(data=summary, x="origem", y="registros", hue="origem", palette=PALETTE, legend=False)
    axis.set(title="Cobertura por método de rotulagem", xlabel="Método", ylabel="Avaliações")
    for bar, value in zip(axis.patches, summary["percentual"]):
        axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.1f}%", ha="center", va="bottom")
    save_figure(output_dir, "01_cobertura_rotulos.png")
    return summary


def plot_intent_distribution(data: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    summary = data["intent"].value_counts().rename_axis("intencao").reset_index(name="registros")
    summary["percentual"] = summary["registros"] / len(data) * 100
    plt.figure(figsize=(11, 9))
    axis = sns.barplot(data=summary, y="intencao", x="registros", color="#2563EB")
    axis.set(title="Distribuição das categorias principais", xlabel="Avaliações", ylabel="Categoria")
    for bar, value in zip(axis.patches, summary["percentual"]):
        axis.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {value:.1f}%", va="center")
    save_figure(output_dir, "02_distribuicao_intencoes.png")
    return summary


def plot_rating_by_intent(data: pd.DataFrame, output_dir: Path, intent_summary: pd.DataFrame) -> None:
    selected = intent_summary.head(15)["intencao"].tolist()
    matrix = pd.crosstab(data["intent"], data["overall_rating"], normalize="index").mul(100).reindex(selected)
    plt.figure(figsize=(10, 8))
    sns.heatmap(matrix, annot=True, fmt=".0f", cmap="Blues", cbar_kws={"label": "% dentro da categoria"})
    plt.title("Distribuição de notas por categoria (15 maiores)")
    plt.xlabel("Nota")
    plt.ylabel("Categoria")
    save_figure(output_dir, "03_notas_por_intencao.png")


def plot_text_length(data: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(8, 5))
    axis = sns.boxplot(data=data, x="label_source", y="word_count", hue="label_source", palette=PALETTE, legend=False)
    axis.set(title="Extensão do texto por origem do rótulo", xlabel="Método", ylabel="Palavras")
    axis.set_ylim(0, data["word_count"].quantile(0.95))
    save_figure(output_dir, "04_tamanho_texto_por_origem.png")


def plot_sentiment(data: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    order = ["positivo", "neutro", "negativo", "misto"]
    summary = data["sentiment"].value_counts().reindex(order, fill_value=0).rename_axis("sentimento").reset_index(name="registros")
    colors = {"positivo": "#059669", "neutro": "#64748B", "negativo": "#DC2626", "misto": "#7C3AED"}
    plt.figure(figsize=(8, 5))
    axis = sns.barplot(data=summary, x="sentimento", y="registros", hue="sentimento", palette=colors, legend=False)
    axis.set(title="Distribuição de sentimento, separado do tema", xlabel="Sentimento", ylabel="Avaliações")
    save_figure(output_dir, "07_distribuicao_sentimento.png")
    return summary


def plot_cooccurrence(data: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    pairs: list[tuple[str, str]] = []
    for value in data["intent_matches"].dropna():
        matches = value.split("|")
        pairs.extend(combinations(matches, 2))
    summary = pd.Series(pairs).value_counts().head(15).rename_axis("par").reset_index(name="registros")
    if summary.empty:
        return summary
    summary["par"] = summary["par"].map(lambda pair: " + ".join(pair))
    plt.figure(figsize=(11, 7))
    axis = sns.barplot(data=summary, y="par", x="registros", color="#7C3AED")
    axis.set(title="Coocorrências mais frequentes de temas", xlabel="Avaliações", ylabel="Par de temas")
    save_figure(output_dir, "05_coocorrencias.png")
    return summary


def plot_monthly_trends(data: pd.DataFrame, output_dir: Path, intent_summary: pd.DataFrame) -> None:
    dated = data.dropna(subset=["submission_date"]).copy()
    if dated.empty:
        return
    selected = intent_summary.head(8)["intencao"].tolist()
    dated = dated[dated["intent"].isin(selected)]
    dated["mes"] = dated["submission_date"].dt.to_period("M").dt.to_timestamp()
    monthly = dated.groupby(["mes", "intent"]).size().rename("registros").reset_index()
    plt.figure(figsize=(11, 5))
    sns.lineplot(data=monthly, x="mes", y="registros", hue="intent", marker="o")
    plt.title("Evolução mensal das oito maiores categorias")
    plt.xlabel("Mês de submissão")
    plt.ylabel("Avaliações")
    plt.legend(title="Categoria", bbox_to_anchor=(1.02, 1), loc="upper left")
    save_figure(output_dir, "06_evolucao_mensal.png")


def write_report(data: pd.DataFrame, output_dir: Path, coverage: pd.DataFrame, intents: pd.DataFrame, sentiments: pd.DataFrame, pairs: pd.DataFrame) -> None:
    temporal = data["submission_date"].dropna()
    multi_intent = data["intent_matches"].fillna("").str.contains("\\|").sum()
    lines = [
        "# Relatório de EDA — B2W Intents v4", "",
        "Este relatório é gerado automaticamente por `scripts/generate_b2w_eda.py`.", "",
        "## Integridade", "",
        f"- Registros: {len(data):,}",
        f"- Duplicatas exatas no Parquet: {data.duplicated().sum():,}",
        f"- Texto vazio: {data['text'].fillna('').str.strip().eq('').sum():,}",
        f"- Avaliações com múltiplos temas textuais: {multi_intent:,}",
        f"- Período: {temporal.min():%Y-%m-%d} a {temporal.max():%Y-%m-%d}" if not temporal.empty else "- Período: indisponível",
        "", "## Cobertura por origem", "", "| Origem | Registros | Percentual |", "| --- | ---: | ---: |",
    ]
    lines += [f"| `{row.origem}` | {row.registros:,} | {row.percentual:.2f}% |" for row in coverage.itertuples(index=False)]
    lines += ["", "## Categorias principais", "", "| Categoria | Registros | Percentual |", "| --- | ---: | ---: |"]
    lines += [f"| `{row.intencao}` | {row.registros:,} | {row.percentual:.2f}% |" for row in intents.itertuples(index=False)]
    lines += ["", "## Sentimento", "", "| Sentimento | Registros |", "| --- | ---: |"]
    lines += [f"| `{row.sentimento}` | {row.registros:,} |" for row in sentiments.itertuples(index=False)]
    if not pairs.empty:
        lines += ["", "## Coocorrências principais", "", "| Par | Registros |", "| --- | ---: |"]
        lines += [f"| {row.par} | {row.registros:,} |" for row in pairs.itertuples(index=False)]
    (output_dir / "relatorio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/b2w_reviews_intents.parquet"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/b2w_intents"))
    args = parser.parse_args()
    data = load_dataset(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    coverage = plot_label_coverage(data, args.output_dir)
    intents = plot_intent_distribution(data, args.output_dir)
    plot_rating_by_intent(data, args.output_dir, intents)
    plot_text_length(data, args.output_dir)
    sentiments = plot_sentiment(data, args.output_dir)
    pairs = plot_cooccurrence(data, args.output_dir)
    plot_monthly_trends(data, args.output_dir, intents)
    write_report(data, args.output_dir, coverage, intents, sentiments, pairs)
    print(f"EDA gerada em: {args.output_dir}")


if __name__ == "__main__":
    main()
