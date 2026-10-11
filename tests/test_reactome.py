import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, false_discovery_control

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/GSE156496/deseq2"


class ReactomeIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.de = pd.read_csv(OUT / "deseq2_D51_vs_WT_unshrunken.csv")
        cls.mapping = pd.read_csv(ROOT / "data/annotations/reactome_v95_mouse.tsv", sep="\t")
        cls.table = pd.read_csv(OUT / "reactome_enrichment.csv")
        cls.provenance = json.loads((OUT / "reactome_provenance.json").read_text())

    def test_annotation_hash_species_background(self):
        path = ROOT / "data/annotations/reactome_v95_mouse.tsv"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.provenance["mouse_mapping_sha256"])
        self.assertEqual(set(self.mapping.species), {"Mus musculus"})
        self.assertTrue(self.mapping.gene_id.str.fullmatch(r"ENSMUSG\d+").all())
        universe = set(self.de.loc[self.de.padj.notna(), "gene_id"]) & set(self.mapping.gene_id)
        self.assertEqual(len(universe), self.provenance["mapped_background"])
        self.assertEqual(set(self.table.universe_size), {len(universe)})

    def test_hypergeometric_and_bh_per_direction(self):
        for _, table in self.table.groupby("direction"):
            expected = hypergeom.sf(table.overlap - 1, table.universe_size, table.pathway_size, table.selected_size)
            np.testing.assert_allclose(table.pvalue, expected, rtol=1e-10, atol=1e-15)
            np.testing.assert_allclose(table.padj, false_discovery_control(table.pvalue.to_numpy(), method="bh"), rtol=1e-10, atol=1e-15)
            self.assertTrue((table.overlap == 0).any(), "Zero-overlap terms must be included in FDR family")

    def test_gene_overlaps_and_term_filter(self):
        universe = set(self.de.loc[self.de.padj.notna(), "gene_id"]) & set(self.mapping.gene_id)
        sets = {key:set(group.gene_id) & universe for key,group in self.mapping.groupby("pathway_id")}
        deg = self.de[(self.de.padj < .05) & (self.de.log2FoldChange.abs() > 1)]
        for direction, table in self.table.groupby("direction"):
            selected = deg if direction == "all" else deg[deg.log2FoldChange > 0] if direction == "up" else deg[deg.log2FoldChange < 0]
            selected_ids = set(selected.gene_id) & universe
            self.assertEqual(set(table.pathway_id), {key for key,genes in sets.items() if 10<=len(genes)<=500})
            for row in table.itertuples():
                self.assertEqual(row.overlap, len(sets[row.pathway_id] & selected_ids))
                self.assertEqual(row.selected_size, len(selected_ids))


if __name__ == "__main__":
    unittest.main()
