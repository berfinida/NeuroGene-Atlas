import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from backend.main import app

ROOT = Path(__file__).resolve().parents[1]


class Phase5API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_all_study_metadata_counts_and_groups(self):
        for study, number, degs in [("GSE156496", 6, 1499), ("GSE132741", 15, 2419), ("GSE284723", 9, 1817)]:
            response = self.client.get(f"/api/studies/{study}")
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(len(body["samples"]), number)
            self.assertEqual(len(body["pca"]), number)
            self.assertEqual(body["summary"]["degs"], degs)
            counts = pd.read_csv(ROOT / "data/processed" / study / "count_matrix.csv", index_col=0)
            self.assertEqual(body["summary"]["prepared_genes"], len(counts))
            for sample in body["samples"]:
                self.assertEqual(sample["library_size"], counts[sample["count_column"]].sum())
                self.assertLessEqual(sample["fitted_library_size"], sample["library_size"])
            if study == "GSE284723":
                self.assertIn("not WT", body["cohort"]["reference"])

    def test_study_downloads_match_original_bytes(self):
        for study in ("GSE156496", "GSE132741", "GSE284723"):
            for artifact in ("counts", "metadata", "unshrunken", "apeglm", "pca", "distances", "session"):
                response = self.client.get(f"/api/studies/{study}/download/{artifact}")
                self.assertEqual(response.status_code, 200)
                self.assertIn(study, response.headers["content-disposition"])
                self.assertGreater(len(response.content), 100)
                if artifact == "counts":
                    self.assertEqual(response.content, (ROOT / "data/processed" / study / "count_matrix.csv").read_bytes())
                elif artifact in ("unshrunken", "apeglm"):
                    name = f"deseq2_D51_vs_WT_{artifact}.csv" if study == "GSE156496" else f"{artifact}.csv"
                    self.assertEqual(response.content, (ROOT / "results" / study / "deseq2" / name).read_bytes())

    def test_study_input_validation(self):
        for route in ("studies/unknown", "studies/GSE284723/download/unknown", "gene-search", "gene-search?q="):
            self.assertEqual(self.client.get("/api/" + route).status_code, 422)

    def test_missing_figure_is_404_not_runtime_exception(self):
        with tempfile.TemporaryDirectory() as folder, patch("backend.main.OUT", Path(folder)):
            self.assertEqual(self.client.get("/api/figures/pca.png").status_code, 404)

    def test_literal_search_and_parameter_validation(self):
        self.assertEqual(self.client.get("/api/genes?q=[.*").json()["total"], 0)
        self.assertEqual(self.client.get("/api/evidence?q=[.*").json()["total"], 0)
        for route in ("network?confidence=nan", "network?confidence=1.1", "evidence?limit=101",
                      "statistical-sensitivity?study_a=GSE132741&study_b=GSE132741", "expression/UNKNOWN"):
            expected = 404 if route == "expression/UNKNOWN" else 422
            self.assertEqual(self.client.get("/api/" + route).status_code, expected)

    def test_qc_distance_and_pca_identity(self):
        for study in ("GSE156496", "GSE132741", "GSE284723"):
            body = self.client.get(f"/api/studies/{study}").json()
            distances = pd.DataFrame(body["distances"])
            np.testing.assert_allclose(distances, distances.T)
            np.testing.assert_allclose(np.diag(distances), 0)
            self.assertEqual(set(distances), {s["count_column"] for s in body["samples"]})
            stored = pd.read_csv(ROOT / "results/phase4/qc" / f"{study}_pca.csv")
            np.testing.assert_allclose([p["PC1"] for p in body["pca"]], stored.PC1)

    def test_final_audit_and_document_exports(self):
        from backend.main import FINAL_DOCUMENTS
        body = self.client.get("/api/final-audit").json()
        self.assertEqual(body["phase"], 5)
        self.assertEqual(body["matched_tables"], 24)
        self.assertEqual(body["reproduction_status"], "passed")
        for name in FINAL_DOCUMENTS:
            response = self.client.get(f"/api/final/download/{name}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, (ROOT / name).read_bytes())
        self.assertEqual(self.client.get("/api/final/download/requirements.lock.txt").status_code, 404)

    def test_final_report_signatures_and_real_figures(self):
        for extension, signature in [("html", b"<!doctype html>"), ("pdf", b"%PDF")]:
            response = self.client.get(f"/api/final/download/NeuroGene_Atlas_Scientific_Report_FINAL.{extension}")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content.startswith(signature))
        html = self.client.get("/api/final/download/NeuroGene_Atlas_Scientific_Report_FINAL.html").text
        self.assertEqual(html.count('src="data:image/png;base64,'), 14)


class Phase5Integrity(unittest.TestCase):
    def test_final_reports_data_and_limitations(self):
        from pypdf import PdfReader
        document = (ROOT / "FINAL_SCIENTIFIC_AUDIT.md").read_text()
        for value in ("976", "973", "75.2868%", "99.6926%", "572", "555", "same-host", "not"):
            self.assertIn(value, document)
        pdf = PdfReader(ROOT / "results/reports/NeuroGene_Atlas_Scientific_Report_FINAL.pdf")
        text = " ".join(p.extract_text() for p in pdf.pages)
        for value in ("Final Scientific Audit", "Publication Readiness", "Candidate Gene Evidence", "976", "973", "1,817", "24"):
            self.assertIn(value, text)
        self.assertGreater(len(pdf.pages), 5)

    def test_final_document_copies_and_inventory(self):
        import re
        from backend.main import FINAL_DOCUMENTS
        def public_copy(text):
            # Only redact historical machine paths; all scientific text must match.
            text = re.sub(r"(?m)^Exact observed executable paths.*$",
                          "Exact executable paths and command ledgers are retained in private local audit records, not in the public source. The commands below are portable equivalents, not a claim that the deleted `.venv` was used in this audit. Python used a fresh temporary environment; Node v22.23.1.", text)
            return re.sub(r"--rscript \S+", "--rscript Rscript", text)
        for name in FINAL_DOCUMENTS:
            self.assertEqual(public_copy((ROOT / name).read_text()),
                             public_copy((ROOT / "results/final/audit" / name).read_text()))
        inventory = json.loads((ROOT / "results/validation/phase5/inventory.json").read_text())
        self.assertEqual(len(inventory["modules"]), 12)
        self.assertTrue(all(m["implemented"] and m["limits"] for m in inventory["modules"]))

    def test_fresh_isolated_reproduction(self):
        record = json.loads((ROOT / "results/validation/phase5/reproduction.json").read_text())
        self.assertEqual(record["status"], "passed")
        self.assertEqual(sum(len(s["tables"]) for s in record["studies"].values()), 24)
        for name, expected in record["original_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
        for study in record["studies"].values():
            self.assertTrue(all(t["matched"] for t in study["tables"].values()))
        self.assertTrue(all(c["exit_code"] == 0 for c in record["commands"]))

    def test_selection_statistics_recomputed_from_study_results(self):
        sources = {}
        for study in ("GSE156496", "GSE132741", "GSE284723"):
            name = "deseq2_D51_vs_WT_unshrunken.csv" if study == "GSE156496" else "unshrunken.csv"
            sources[study] = pd.read_csv(ROOT / "results" / study / "deseq2" / name).set_index("gene_id")
        selection = pd.read_csv(ROOT / "results/phase4/selection_audit.csv")
        for (a, b), rows in selection.groupby(["study_a", "study_b"]):
            frame = sources[a].join(sources[b], how="inner", lsuffix="_a", rsuffix="_b")
            frame = frame[np.isfinite(frame.log2FoldChange_a) & np.isfinite(frame.log2FoldChange_b)]
            for subset in ("all_common_finite_effects", "common_valid_FDR", "study_a_selected", "DEG_intersection"):
                f = frame.copy()
                if subset != "all_common_finite_effects":
                    f = f.dropna(subset=["padj_a", "padj_b"])
                if subset in ("study_a_selected", "DEG_intersection"):
                    f = f[(f.padj_a < .05) & (f.log2FoldChange_a.abs() > 1)]
                if subset == "DEG_intersection":
                    f = f[(f.padj_b < .05) & (f.log2FoldChange_b.abs() > 1)]
                row = rows[rows.subset == subset].iloc[0]
                self.assertEqual(len(f), row.genes)
                self.assertAlmostEqual(float((np.sign(f.log2FoldChange_a) == np.sign(f.log2FoldChange_b)).mean()), row.sign_concordance, places=9)
                self.assertAlmostEqual(pearsonr(f.log2FoldChange_a, f.log2FoldChange_b).statistic, row.pearson_r, places=9)
                self.assertAlmostEqual(spearmanr(f.log2FoldChange_a, f.log2FoldChange_b).statistic, row.spearman_rho, places=9)

    def test_candidate_fixed_denominator_and_rank_ties(self):
        ranks = pd.read_csv(ROOT / "results/discovery/candidates/rankings.csv")
        methods = json.loads((ROOT / "results/discovery/candidates/methods.json").read_text())
        weights = methods["weight_presets"] if "weight_presets" in methods else methods["weights"]
        for preset, values in weights.items():
            score = sum(ranks[key].fillna(0) * weight for key, weight in values.items()) / sum(values.values())
            np.testing.assert_allclose(score, ranks[f"score_{preset}"], atol=1e-12)
            ordered = ranks.sort_values([f"score_{preset}", "gene_id"], ascending=[False, True])
            np.testing.assert_array_equal(ordered[f"rank_{preset}"], np.arange(1, len(ranks) + 1))

    def test_stable_context_flags_recomputed(self):
        evidence = pd.read_csv(ROOT / "results/phase4/candidate_evidence.csv").set_index("gene_id")
        adjusted = pd.read_csv(ROOT / "results/phase4/unshrunken_fasting_adjusted.csv").set_index("gene_id").reindex(evidence.index)
        supported = evidence.three_study_filter_outlier_stable & (adjusted.padj < .05) & (adjusted.log2FoldChange.abs() > 1) & (np.sign(adjusted.log2FoldChange) == np.sign(evidence.log2FoldChange))
        self.assertEqual(int(supported.sum()), 555)

    def test_network_one_to_one_mapping_and_no_added_nodes(self):
        folder = ROOT / "results/discovery/network"
        mapping = pd.read_csv(folder / "mapping.csv")
        self.assertTrue(mapping.gene_id.is_unique)
        self.assertTrue(mapping.stringId.is_unique)
        edges = pd.read_csv(folder / "edges.csv")
        self.assertTrue(set(edges.source) | set(edges.target) <= set(mapping.gene_id))
        self.assertEqual(len(edges), 17872)
        self.assertFalse((edges.source == edges.target).any())


if __name__ == "__main__":
    unittest.main()
