#!/usr/bin/env python3
"""Create a stratified, PII-masked sample for human validation of B2W labels."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REVIEW_COLUMNS = [
    "source_row_id", "text", "intent", "intent_matches", "label_source",
    "sentiment", "sentiment_source", "overall_rating",
]


def sample_per_group(data: pd.DataFrame, group: str, per_group: int, random_state: int) -> pd.DataFrame:
    samples = [
        rows.sample(n=min(len(rows), per_group), random_state=random_state)
        for _, rows in data.groupby(group)
    ]
    return pd.concat(samples, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/b2w_reviews_intents.parquet"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/b2w_manual_review_sample.csv"))
    parser.add_argument("--per-intent", type=int, default=25)
    parser.add_argument("--per-sentiment", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    data = pd.read_parquet(args.input)
    missing = set(REVIEW_COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")

    by_intent = sample_per_group(data, "intent", args.per_intent, args.seed)
    by_sentiment = sample_per_group(data, "sentiment", args.per_sentiment, args.seed)
    sample = pd.concat([by_intent, by_sentiment], ignore_index=True).drop_duplicates(subset="source_row_id")
    sample = sample[REVIEW_COLUMNS].sort_values(["intent", "sentiment", "source_row_id"]).reset_index(drop=True)
    sample["reviewed_by"] = pd.NA
    sample["reviewed_intent"] = pd.NA
    sample["reviewed_sentiment"] = pd.NA
    sample["is_intent_correct"] = pd.NA
    sample["is_sentiment_correct"] = pd.NA
    sample["review_notes"] = pd.NA
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(args.output, index=False)
    print(f"Amostra criada: {args.output} ({len(sample):,} linhas)")


if __name__ == "__main__":
    main()
