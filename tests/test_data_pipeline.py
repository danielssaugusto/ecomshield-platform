"""Small, offline checks for the data pipeline's leakage and sampling rules."""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_bitext_intent_dataset import stable_splits
from create_ptbr_validation_queue import select_sample, stable_id
from evaluate_ptbr_external import subgroup_accuracy, summarize_predictions


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
        disagreement = labels["intent_a"].ne(labels["intent_b"])
        eligible = labels["uncertain_a"].ne("yes") & labels["uncertain_b"].ne("yes")
        final_intent = labels["intent_a"].where(~disagreement, labels["adjudicated_intent"])
        self.assertEqual(int(eligible.sum()), 422)
        self.assertEqual(final_intent.nunique(), 20)
        self.assertEqual(final_intent[eligible].nunique(), 14)
        self.assertEqual(int(final_intent[eligible].eq("submit_product_feedback").sum()), 292)
        self.assertEqual(int((disagreement & labels["adjudication_notes"].eq("")).sum()), 84)
        self.assertEqual(int((disagreement & eligible & labels["adjudication_notes"].eq("")).sum()), 60)

    def test_external_metrics_do_not_score_classes_without_support(self) -> None:
        result = summarize_predictions(
            ["feedback", "feedback", "delivery"],
            ["feedback", "other", "other"],
            ["delivery", "feedback", "other"],
        )
        self.assertEqual(result["eligible_rows"], 3)
        self.assertEqual(result["correct_rows"], 1)
        self.assertEqual(result["supported_intents"], 2)
        self.assertEqual(result["unsupported_intents"], ["other"])
        self.assertEqual(result["predictions_for_unsupported_intents"], 2)
        self.assertAlmostEqual(result["accuracy"], 1 / 3)
        self.assertAlmostEqual(result["majority_baseline_accuracy"], 2 / 3)
        self.assertNotIn("other", result["per_intent"])

    def test_external_metrics_reject_taxonomy_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            summarize_predictions(["feedback"], ["unknown"], ["feedback"])

    def test_external_subgroups_are_descriptive_and_reconcile(self) -> None:
        groups = subgroup_accuracy(
            ["a", "a", "b"], ["a", "b", "b"], ["agreed", "agreed", "adjudicated"]
        )
        self.assertEqual(groups["agreed"]["rows"], 2)
        self.assertEqual(groups["agreed"]["correct"], 1)
        self.assertAlmostEqual(groups["agreed"]["accuracy"], 0.5)
        self.assertEqual(sum(row["rows"] for row in groups.values()), 3)
        with self.assertRaises(ValueError):
            subgroup_accuracy(["a"], ["a"], [])

    def test_external_report_records_reconcile_with_summary(self) -> None:
        root = Path(__file__).resolve().parents[1]
        report = json.loads((root / "reports/tp3_data/avaliacao_externa_ptbr.json").read_text())
        rows = report["records"]
        summary = report["summary"]
        self.assertEqual(len(rows), summary["eligible_rows"])
        self.assertEqual(len({row["sample_id"] for row in rows}), len(rows))
        self.assertEqual(sum(row["actual"] == row["predicted"] for row in rows), summary["correct_rows"])
        self.assertEqual(sum(row["recognized_features"] == 0 for row in rows), report["provenance"]["empty_feature_vectors"])
        self.assertEqual(len({row["actual"] for row in rows}), summary["supported_intents"])
        self.assertFalse(any("feedback_text" in row for row in rows))

    def test_multilingual_transfer_keeps_external_data_out_of_selection(self) -> None:
        root = Path(__file__).resolve().parents[1]
        payload = json.loads((root / "reports/tp3_data/transferencia_multilingue.json").read_text())
        provenance = payload["provenance"]
        rows = payload["predictions"]
        summary = payload["external"]
        self.assertFalse(provenance["used_ptbr_for_training_or_selection"])
        self.assertEqual(provenance["selection_metric"], "Bitext validation macro-F1")
        self.assertEqual(provenance["selected_C"], max(
            payload["bitext_validation"], key=lambda row: (row["macro_f1"], -row["C"])
        )["C"])
        self.assertEqual(len(rows), 422)
        self.assertEqual(len({row["sample_id"] for row in rows}), 422)
        self.assertEqual(sum(row["actual"] == row["predicted"] for row in rows), summary["correct_rows"])
        self.assertEqual(len({row["actual"] for row in rows}), summary["supported_intents"])
        self.assertFalse(any("feedback_text" in row for row in rows))
        baseline = json.loads((root / "reports/tp3_data/avaliacao_externa_ptbr.json").read_text())
        self.assertEqual(provenance["ptbr_sha256"], baseline["provenance"]["external_dataset_sha256"])


if __name__ == "__main__":
    unittest.main()
