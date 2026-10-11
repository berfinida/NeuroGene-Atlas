import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/GSE156496/deseq2"


class DESeq2Integrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((OUT / "summary.json").read_text())
        cls.raw = pd.read_csv(OUT / "deseq2_D51_vs_WT_unshrunken.csv").set_index("gene_id")
        cls.shrunk = pd.read_csv(OUT / "deseq2_D51_vs_WT_apeglm.csv").set_index("gene_id")
        cls.counts = pd.read_csv(ROOT / "data/processed/GSE156496/count_matrix.csv", index_col=0)

    def test_filter_and_identifiers(self):
        expected = self.counts.index[(self.counts >= 10).sum(axis=1) >= 3]
        self.assertListEqual(expected.tolist(), self.raw.index.tolist())
        self.assertTrue(self.raw.index.is_unique)
        self.assertTrue(self.raw.index.str.fullmatch(r"ENSMUSG\d+").all())
        self.assertFalse(self.raw.gene_symbol.isna().any())

    def test_bh_adjustment(self):
        tested = self.raw.dropna(subset=["padj"])
        order = np.argsort(tested.pvalue.to_numpy())
        p = tested.pvalue.to_numpy()[order]
        expected = np.minimum(1, np.minimum.accumulate((p * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1])
        np.testing.assert_allclose(tested.padj.to_numpy()[order], expected, atol=1e-12)

    def test_statistical_ranges_and_wald_stat(self):
        for field in ["pvalue", "padj"]:
            self.assertTrue(self.raw[field].dropna().between(0, 1).all())
        self.assertTrue((self.raw.baseMean >= 0).all())
        self.assertTrue((self.raw.lfcSE.dropna() > 0).all())
        np.testing.assert_allclose(self.raw.stat, self.raw.log2FoldChange / self.raw.lfcSE, rtol=1e-9)

    def test_shrinkage_preserves_inference(self):
        self.assertListEqual(self.raw.index.tolist(), self.shrunk.index.tolist())
        for field in ["pvalue", "padj", "baseMean"]:
            np.testing.assert_allclose(self.raw[field], self.shrunk[field], equal_nan=True)
        self.assertFalse(np.allclose(self.raw.log2FoldChange, self.shrunk.log2FoldChange))

    def test_normalization_and_direction(self):
        meta = pd.read_csv(OUT / "sample_metadata.csv")
        normalized = pd.read_csv(OUT / "normalized_counts.csv", index_col=0)
        self.assertListEqual(meta.count_column.tolist(), normalized.columns.tolist())
        expected = self.counts.loc[self.raw.index].to_numpy() / meta.size_factor.to_numpy()
        np.testing.assert_allclose(normalized, expected, rtol=1e-12)
        np.testing.assert_allclose(normalized.mean(axis=1), self.raw.baseMean, rtol=1e-12)
        self.assertEqual(self.summary["contrast"], "D51_vs_WT")
        self.assertTrue(self.summary["validation"]["contrast_reversal"])
        # The normalized group ratio should agree with model direction for strong effects.
        ratio = np.log2((normalized.iloc[:, 3:].mean(axis=1) + 1) / (normalized.iloc[:, :3].mean(axis=1) + 1))
        strong = self.raw.log2FoldChange.abs() > 1
        self.assertGreater((np.sign(ratio[strong]) == np.sign(self.raw.log2FoldChange[strong])).mean(), 0.99)

    def test_summary_counts(self):
        selected = (self.raw.padj < 0.05) & (self.raw.log2FoldChange.abs() > 1)
        self.assertEqual(int(selected.sum()), self.summary["significant_padj_0_05_abs_lfc_1"])
        self.assertEqual(len(self.raw), self.summary["genes_tested"])
        self.assertTrue(all(self.summary["validation"].values()))

    def test_pca_and_sample_distance(self):
        pca = pd.read_csv(OUT / "pca_samples.csv")
        self.assertEqual(len(pca), 6)
        self.assertTrue(np.isfinite(pca[["PC1", "PC2"]]).all().all())
        distance = pd.read_csv(OUT / "sample_distances.csv", index_col=0).to_numpy()
        np.testing.assert_allclose(distance, distance.T)
        np.testing.assert_allclose(np.diag(distance), 0)
        self.assertTrue((distance >= 0).all())

    def test_figures_and_session(self):
        for name in ["pca", "volcano", "ma", "heatmap", "sample_distance"]:
            for suffix in ["png", "pdf"]:
                self.assertGreater((OUT / "figures" / f"{name}.{suffix}").stat().st_size, 1000)
        self.assertIn("DESeq2", (OUT / "sessionInfo.txt").read_text())


if __name__ == "__main__":
    unittest.main()
