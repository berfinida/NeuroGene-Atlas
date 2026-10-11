import json
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class PhaseAOutputsTest(unittest.TestCase):
    def test_manifest_and_metadata_match_expected_samples(self):
        manifest_path = ROOT / "results" / "GSE156496" / "analysis_manifest.json"
        self.assertTrue(manifest_path.exists(), "Run scripts/rna_seq/phase_a_gse156496.py first.")
        manifest = json.loads(manifest_path.read_text())
        expected = manifest["config"]["expected_samples"]
        metadata = pd.read_csv(ROOT / "data" / "processed" / "GSE156496" / "sample_metadata.csv")
        self.assertEqual([row["geo_accession"] for row in expected], metadata["geo_accession"].tolist())
        self.assertEqual(["WT", "WT", "WT", "D51", "D51", "D51"], metadata["condition"].tolist())

    def test_count_matrix_contains_integer_counts(self):
        counts = pd.read_csv(ROOT / "data" / "processed" / "GSE156496" / "count_matrix.csv", index_col=0)
        self.assertEqual(counts.shape[1], 6)
        self.assertTrue((counts >= 0).all().all())
        self.assertTrue(((counts % 1) == 0).all().all())


if __name__ == "__main__":
    unittest.main()
