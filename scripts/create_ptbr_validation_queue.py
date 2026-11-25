#!/usr/bin/env python3
"""Create a blinded, reproducible queue for human PT-BR intent annotation.

This script samples real B2W feedback. It deliberately leaves every intent
field blank: filling it algorithmically would recreate the label-leakage issue
identified in the project review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from download_b2w_reviews import ensure_b2w_source


def normalized_feedback(frame: pd.DataFrame) -> pd.DataFrame:
    title = frame["review_title"].fillna("").astype(str)
    body = frame["review_text"].fillna("").astype(str)
    result = pd.DataFrame({
        "feedback_text": (title + " " + body).map(lambda text: " ".join(text.split())),
        "overall_rating": pd.to_numeric(frame["overall_rating"], errors="coerce"),
    })
    return result[result["feedback_text"].ne("")].drop_duplicates(subset=["feedback_text"]).copy()


def stable_id(text: str) -> str:
    return "b2w-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def select_sample(raw: pd.DataFrame, per_rating: int = 100, seed: int = 42) -> pd.DataFrame:
    """Select the same blinded, rating-balanced sample on every run."""
    clean = normalized_feedback(raw)
    parts: list[pd.DataFrame] = []
    for rating in range(1, 6):
        candidates = clean[clean["overall_rating"] == rating]
        if len(candidates) < per_rating:
            raise ValueError(f"Há somente {len(candidates)} avaliações com nota {rating}.")
        parts.append(candidates.sample(n=per_rating, random_state=seed + rating))
    return pd.concat(parts, ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw/b2w-reviews01/B2W-Reviews01.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/annotations/ptbr_intent_validation_queue.csv"))
    parser.add_argument("--metadata", type=Path, default=Path("data/annotations/ptbr_intent_validation_queue_metadata.json"))
    parser.add_argument("--bitext-dataset", type=Path, default=Path("data/processed/bitext_retail_intents.parquet"))
    parser.add_argument("--per-rating", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.per_rating <= 0:
        raise ValueError("--per-rating precisa ser positivo.")

    raw = pd.read_csv(ensure_b2w_source(args.input), low_memory=False)
    bitext = pd.read_parquet(args.bitext_dataset)
    if not {"intent", "category"}.issubset(bitext.columns):
        raise ValueError("O dataset Bitext precisa conter as colunas intent e category.")
    sample = select_sample(raw, per_rating=args.per_rating, seed=args.seed)
    queue = pd.DataFrame({
        "sample_id": sample["feedback_text"].map(stable_id),
        "feedback_text": sample["feedback_text"],
        "intent": "",
        "uncertain": "",
        "notes": "",
    })
    if not queue["sample_id"].is_unique:
        raise AssertionError("IDs de amostra precisam ser únicos.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    queue.to_csv(args.output, index=False)
    args.metadata.write_text(json.dumps({
        "source": "B2W-Reviews01",
        "seed": args.seed,
        "per_rating": args.per_rating,
        "total_rows": len(queue),
        "sampling": "Amostragem estratificada por overall_rating; a nota não é entregue aos anotadores.",
        "labels_created_by_script": False,
        "bitext_intents": sorted(bitext["intent"].dropna().astype(str).unique().tolist()),
        "bitext_categories": sorted(bitext["category"].dropna().astype(str).unique().tolist()),
        "columns": queue.columns.tolist(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fila sem rótulos criada: {args.output} ({len(queue)} textos)")


if __name__ == "__main__":
    main()
