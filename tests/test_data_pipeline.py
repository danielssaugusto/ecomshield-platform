"""Small, offline checks for the data pipeline's leakage and sampling rules."""

from __future__ import annotations

import sys
import unittest
import hashlib
import json
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_bitext_intent_dataset import stable_splits  # noqa: E402
from create_ptbr_validation_queue import select_sample, stable_id  # noqa: E402


class DataPipelineTests(unittest.TestCase):
    def test_identical_text_stays_in_one_split(self) -> None:
        rows = []
        for intent in ("alpha", "beta"):
            for number in range(30):
                rows.append({"text": f"{intent}-{number}", "intent": intent, "record_id": f"{intent}-{number:02}"})
            rows.append({"text": f"{intent}-0", "intent": intent, "record_id": f"{intent}-duplicate"})
        frame = pd.DataFrame(rows)
        frame["split"] = stable_splits(frame)
        self.assertEqual(int(frame.groupby("text")["split"].nunique().gt(1).sum()), 0)
        self.assertTrue((frame.groupby("intent")["split"].nunique() == 3).all())
        self.assertTrue(frame["split"].equals(stable_splits(frame)))

    def test_conflicting_labels_for_identical_text_are_rejected(self) -> None:
        frame = pd.DataFrame({
            "text": ["same", "same"],
            "intent": ["alpha", "beta"],
            "record_id": ["one", "two"],
        })
        with self.assertRaises(ValueError):
            stable_splits(frame)

    def test_blinded_b2w_sample_is_deterministic_and_balanced(self) -> None:
        raw = pd.DataFrame([
            {"review_title": f"Título {rating}-{number}", "review_text": "Texto", "overall_rating": rating}
            for rating in range(1, 6) for number in range(6)
        ])
        first = select_sample(raw, per_rating=2, seed=42)
        second = select_sample(raw, per_rating=2, seed=42)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first["overall_rating"].value_counts().to_dict(), {rating: 2 for rating in range(1, 6)})
        self.assertEqual(len(set(first["feedback_text"].map(stable_id))), 10)

    def test_versioned_human_labels_match_manifest(self) -> None:
        root = Path(__file__).resolve().parents[1]
        labels_path = root / "data/annotations/ptbr_human_labels.csv"
        manifest = json.loads((root / "data/annotations/ptbr_human_labels.manifest.json").read_text())
        digest = hashlib.sha256(labels_path.read_bytes()).hexdigest()
        labels = pd.read_csv(labels_path, dtype=str, keep_default_na=False)
        self.assertEqual(digest, manifest["labels_sha256"])
        self.assertEqual(len(labels), manifest["rows"])
        self.assertTrue(labels["sample_id"].is_unique)
        self.assertEqual(int(labels["intent_a"].ne(labels["intent_b"]).sum()), manifest["adjudicated"])


if __name__ == "__main__":
    unittest.main()
