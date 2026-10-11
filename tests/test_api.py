import io
import unittest
import zipfile

import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app, OUT, DOWNLOADS


class APIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.de = pd.read_csv(OUT / "deseq2_D51_vs_WT_unshrunken.csv")

    def test_dataset_and_qc(self):
        data = self.client.get("/api/datasets").json()
        self.assertEqual(data["summary"]["genes_tested"], len(self.de))
        self.assertEqual(len(data["samples"]), 6)
        qc = self.client.get("/api/qc").json()
        self.assertEqual(len(qc["pca"]), 6)
        self.assertEqual(qc["summary"], data["summary"])

    def test_filtering_search_pagination_and_export(self):
        expected = self.de[(self.de.padj < .05) & (self.de.log2FoldChange.abs() > 1)].sort_values("padj")
        first = self.client.get("/api/genes").json()
        self.assertEqual(first["total"], len(expected))
        self.assertEqual(first["rows"][0]["gene_id"], expected.iloc[0].gene_id)
        next_page = self.client.get("/api/genes?offset=50").json()
        self.assertEqual(next_page["rows"][0]["gene_id"], expected.iloc[50].gene_id)
        hit = self.client.get("/api/genes?q=Dmd&direction=down").json()
        self.assertEqual(hit["total"], 1)
        self.assertEqual(hit["rows"][0]["gene_id"], "ENSMUSG00000045103")
        up = self.client.get("/api/genes?direction=up").json()
        self.assertEqual(up["total"], 1323)
        export = self.client.get("/api/genes/export?q=Dmd&direction=down")
        self.assertEqual(export.status_code, 200)
        self.assertEqual(len(pd.read_csv(io.StringIO(export.text))), hit["total"])
        self.assertEqual(self.client.get("/api/genes?q=NO_SUCH_GENE").json()["total"], 0)

    def test_expression_all_scales(self):
        for scale, filename in [("normalized", "normalized_counts.csv"), ("vst", "vst_counts.csv")]:
            stored = pd.read_csv(OUT / filename, index_col=0)
            response = self.client.get(f"/api/expression/ENSMUSG00000045103?scale={scale}")
            self.assertEqual(response.status_code, 200)
            for sample in response.json()["samples"]:
                self.assertAlmostEqual(sample["expression"], stored.loc["ENSMUSG00000045103", sample["count_column"]], places=8)
        self.assertEqual(len(self.client.get("/api/expression/ENSMUSG00000045103?scale=raw").json()["samples"]), 6)
        self.assertEqual(self.client.get("/api/expression/INVALID").status_code, 404)
        self.assertEqual(self.client.get("/api/gene-search?q=Dmd").json()[0]["gene_symbol"], "Dmd")

    def test_volcano_and_pathways(self):
        for estimate in ["unshrunken", "apeglm"]:
            response = self.client.get(f"/api/volcano?estimate={estimate}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), self.de.padj.notna().sum())
        paths = self.client.get("/api/pathways").json()
        self.assertEqual(len(paths["rows"]), 48)
        self.assertEqual(paths["provenance"]["mapped_background"], 6893)
        self.assertTrue(all(p["padj"] < .05 for p in paths["rows"]))
        self.assertEqual(self.client.get("/api/pathways?direction=down").json()["rows"], [])

    def test_downloads_figures_and_invalid_parameters(self):
        for name in DOWNLOADS:
            response = self.client.get(f"/api/download/{name}")
            self.assertEqual(response.status_code, 200, name)
            self.assertGreater(len(response.content), 100)
        for name in ["pca", "volcano", "ma", "heatmap", "sample_distance"]:
            for ext, signature in [("png", b"\x89PNG"), ("pdf", b"%PDF")]:
                response = self.client.get(f"/api/figures/{name}.{ext}")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.content.startswith(signature))
        for route in ["genes?padj=0", "genes?lfc=-1", "genes?offset=-1", "genes?estimate=bad", "pathways?direction=bad"]:
            self.assertEqual(self.client.get(f"/api/{route}").status_code, 422)
        self.assertEqual(self.client.get("/api/download/unknown").status_code, 404)
        self.assertEqual(self.client.get("/api/figures/unknown.png").status_code, 404)


if __name__ == "__main__":
    unittest.main()
