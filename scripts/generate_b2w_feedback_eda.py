#!/usr/bin/env python3
"""Generate EDA artifacts for B2W-Reviews01 as real e-commerce feedback.

This analysis intentionally does not create or use an intent column.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from download_b2w_reviews import SOURCE_URL, ensure_b2w_source


TEXT_COLUMN = "feedback_text"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    frame = raw.copy()
    title = frame["review_title"].fillna("").astype(str)
    body = frame["review_text"].fillna("").astype(str)
    frame[TEXT_COLUMN] = (title + " " + body).map(lambda value: " ".join(value.split()))
    without_empty = frame[frame[TEXT_COLUMN].ne("")].copy()
    clean = without_empty.drop_duplicates().copy()
    clean["submission_date"] = pd.to_datetime(clean["submission_date"], errors="coerce")
    clean["text_length_chars"] = clean[TEXT_COLUMN].str.len()
    return clean, {
        "raw_rows": len(raw),
        "rows_removed_empty_text": len(raw) - len(without_empty),
        "rows_removed_duplicates": len(without_empty) - len(clean),
    }


def make_figures(frame: pd.DataFrame, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    missing = frame.isna().sum().sort_values(ascending=False)
    plt.figure(figsize=(10, 5))
    missing.plot.bar(color="#dc2626")
    plt.ylabel("Valores ausentes")
    plt.title("B2W-Reviews01 — valores ausentes após limpeza")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output / "01_valores_ausentes.png", dpi=160)
    plt.close()

    plt.figure(figsize=(7, 4))
    frame["overall_rating"].value_counts().sort_index().plot.bar(color="#2563eb")
    plt.xlabel("Nota")
    plt.ylabel("Avaliações")
    plt.title("Distribuição das notas")
    plt.tight_layout()
    plt.savefig(output / "02_distribuicao_notas.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 6))
    frame["site_category_lv1"].value_counts().head(12).sort_values().plot.barh(color="#0f766e")
    plt.xlabel("Avaliações")
    plt.ylabel("Categoria")
    plt.title("12 categorias com mais avaliações")
    plt.tight_layout()
    plt.savefig(output / "03_categorias_mais_avaliadas.png", dpi=160)
    plt.close()

    monthly = frame.dropna(subset=["submission_date"]).set_index("submission_date").resample("ME").size()
    plt.figure(figsize=(9, 4))
    monthly.plot(marker="o", color="#7c3aed")
    plt.xlabel("Mês")
    plt.ylabel("Avaliações")
    plt.title("Volume mensal de avaliações")
    plt.tight_layout()
    plt.savefig(output / "04_volume_mensal.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    frame.boxplot(column="text_length_chars", by="overall_rating", showfliers=False)
    plt.suptitle("")
    plt.title("Comprimento do texto por nota")
    plt.xlabel("Nota")
    plt.ylabel("Caracteres")
    plt.tight_layout()
    plt.savefig(output / "05_comprimento_por_nota.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    frame["text_length_chars"].clip(upper=1000).plot.hist(bins=40, color="#ea580c")
    plt.xlabel("Caracteres no texto (valores acima de 1.000 agrupados)")
    plt.ylabel("Avaliações")
    plt.title("Distribuição do comprimento das avaliações")
    plt.tight_layout()
    plt.savefig(output / "06_histograma_comprimento_textos.png", dpi=160)
    plt.close()


def write_report(report: dict[str, object], output: Path) -> None:
    summary = report["summary"]
    output.write_text(
        f"""# EDA — B2W-Reviews01 como feedback real

## Escopo

Este relatório analisa avaliações reais de e-commerce em português. O campo de
análise `feedback_text` combina o título e o corpo originais da avaliação.
Nenhuma coluna de intenção é criada ou usada. O B2W complementa o corpus
Bitext, que é o dataset usado para classificação de intenções.

## Integridade

- Fonte: [B2W-Reviews01]({SOURCE_URL})
- Licença da fonte: [CC BY-NC-SA 4.0](https://github.com/americanas-tech/b2w-reviews01); atribuição a B2W Digital, uso não comercial e compartilhamento pela mesma licença.
- SHA-256: `{report["source_sha256"]}`
- Linhas originais: {summary["raw_rows"]:,}
- Textos vazios removidos: {summary["rows_removed_empty_text"]:,}
- Duplicatas exatas removidas: {summary["rows_removed_duplicates"]:,}
- Linhas finais: {summary["final_rows"]:,}
- Período: {summary["period_start"]} a {summary["period_end"]}

## Hipóteses verificadas

1. **As avaliações tendem a notas altas.** A proporção de notas 4 e 5 é
   {summary["high_rating_percent"]:.2f}%.
2. **Textos de notas baixas são mais detalhados.** A mediana de caracteres em
   notas 1–2 é {summary["low_rating_median_length"]:.0f}, contra
   {summary["high_rating_median_length"]:.0f} em notas 4–5.
3. **O volume está concentrado em poucas categorias de produto.** As cinco
   maiores categorias representam {summary["top_five_category_percent"]:.2f}% das avaliações.
4. **A recomendação a amigos acompanha a satisfação declarada.** A taxa de
   recomendação é {summary["recommendation_percent"]:.2f}% entre os registros
   com essa resposta preenchida.

## Figuras

- `01_valores_ausentes.png`
- `02_distribuicao_notas.png`
- `03_categorias_mais_avaliadas.png`
- `04_volume_mensal.png`
- `05_comprimento_por_nota.png`
- `06_histograma_comprimento_textos.png`
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw/b2w-reviews01/B2W-Reviews01.csv"))
    parser.add_argument("--report-json", type=Path, default=Path("data/processed/b2w_feedback_eda_report.json"))
    parser.add_argument("--report-md", type=Path, default=Path("reports/b2w_feedback/relatorio.md"))
    args = parser.parse_args()
    raw = pd.read_csv(ensure_b2w_source(args.input), low_memory=False)
    frame, removals = prepare(raw)
    filled_recommendations = frame["recommend_to_a_friend"].dropna().astype(str).str.lower()
    low = frame[frame["overall_rating"].isin([1, 2])]["text_length_chars"]
    high = frame[frame["overall_rating"].isin([4, 5])]["text_length_chars"]
    top_five = frame["site_category_lv1"].value_counts().head(5).sum()
    report = {
        "dataset_version": "b2w-feedback-eda-v1",
        "source_url": SOURCE_URL,
        "source_sha256": sha256_file(args.input),
        "summary": {
            **removals,
            "final_rows": len(frame),
            "period_start": frame["submission_date"].min().date().isoformat(),
            "period_end": frame["submission_date"].max().date().isoformat(),
            "high_rating_percent": float(frame["overall_rating"].isin([4, 5]).mean() * 100),
            "low_rating_median_length": float(low.median()),
            "high_rating_median_length": float(high.median()),
            "top_five_category_percent": float(top_five / len(frame) * 100),
            "recommendation_percent": float(filled_recommendations.isin(["yes", "sim"]).mean() * 100),
        },
        "missing_values": frame.isna().sum().to_dict(),
        "rating_counts": frame["overall_rating"].value_counts().sort_index().to_dict(),
    }
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    write_report(report, args.report_md)
    make_figures(frame, args.report_md.parent)
    print(f"Relatório B2W gerado: {args.report_md}")


if __name__ == "__main__":
    main()
