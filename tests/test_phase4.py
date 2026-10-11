import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import io
import zipfile

from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control,hypergeom
import networkx as nx

from backend.main import app

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results/phase4"


class Phase4Statistics(unittest.TestCase):
    def test_phase4_documents_and_report(self):
        manuscript=(ROOT/"SCIENTIFIC_MANUSCRIPT_DRAFT.md").read_text()
        for heading in ["Structured Abstract","Introduction","Materials and Methods","Results","Discussion","Limitations","Conclusions","References","Figure Legends","Supplementary Materials"]:
            self.assertIn("## "+heading,manuscript)
        self.assertIn("1,817",manuscript)
        self.assertIn("555",manuscript)
        self.assertIn("selection",(ROOT/"SCIENTIFIC_AUDIT_REPORT.md").read_text().lower())
        from pypdf import PdfReader
        text=" ".join(p.extract_text() for p in PdfReader(ROOT/"results/reports/NeuroGene_Atlas_Scientific_Report.pdf").pages)
        for value in ["Phase 4","1,817","572","555","References","not clinical validation"]:
            self.assertIn(value,text)
        report=(ROOT/"results/reports/NeuroGene_Atlas_Scientific_Report.html").read_text()
        self.assertEqual(report.count('src="data:image/png;base64,'),14)

    def test_original_metadata_and_context(self):
        meta=json.loads((OUT/"original_sample_metadata.json").read_text())
        primary=[r for r in meta if r["study"]=="GSE156496"]
        self.assertEqual(len(primary),6)
        self.assertTrue(all(r["age"]=="1 month" for r in primary))
        self.assertTrue(all("sex" not in r for r in meta))
        context=pd.read_csv(OUT/"external_context.csv")
        self.assertEqual(len(context),15)
        self.assertTrue(context.accession.is_unique)
        self.assertEqual(context.fasting_minutes.min(),274)
        self.assertEqual(context.fasting_minutes.max(),435)
        f=pd.read_csv(OUT/"unshrunken_fasting_adjusted.csv").dropna(subset=["padj"])
        self.assertEqual(len(f),14494)
        baseline=pd.read_csv(ROOT/"results/GSE132741/deseq2/unshrunken_no_replacement.csv")
        self.assertEqual(int(baseline.padj.notna().sum()),13252)
        np.testing.assert_allclose(f.padj,false_discovery_control(f.pvalue),rtol=1e-8,atol=1e-12)
        self.assertEqual(int(((f.padj<.05)&(f.log2FoldChange.abs()>1)).sum()),2958)

    def test_all_candidate_components_recalculated(self):
        f=pd.read_csv(ROOT/"results/discovery/candidates/rankings.csv").set_index("gene_id")
        meta=pd.read_csv(ROOT/"results/GSE156496/deseq2/sample_metadata.csv")
        self.assertEqual(list(meta.condition),["WT"]*3+["D51"]*3)
        counts=pd.read_csv(ROOT/"results/GSE156496/deseq2/normalized_counts.csv",index_col=0).loc[f.index]
        self.assertEqual(list(counts.columns),list(meta.count_column))
        values=counts.to_numpy();sign=np.sign(f.log2FoldChange.to_numpy())
        pairwise=(np.sign(values[:,3:,None]-values[:,None,:3])==sign[:,None,None]).mean(axis=(1,2))
        np.testing.assert_allclose(pairwise,f.consistency)
        np.testing.assert_allclose((-np.log10(f.padj.clip(lower=1e-300))/20).clip(upper=1),f.statistical)
        shrink=pd.read_csv(ROOT/"results/GSE156496/deseq2/deseq2_D51_vs_WT_apeglm.csv").set_index("gene_id")
        np.testing.assert_allclose((shrink.log2FoldChange.reindex(f.index).abs()/3).clip(upper=1),f.effect)
        nodes=pd.read_csv(ROOT/"results/discovery/network/nodes_0.7.csv").set_index("gene_id")
        expected=(np.log1p(nodes.degree)/np.log1p(nodes.degree.max())).reindex(f.index)
        np.testing.assert_allclose(expected,f.network,equal_nan=True)
        comparison=pd.read_csv(ROOT/"results/discovery/replication/gene_comparison.csv").set_index("gene_id")
        expected=comparison.direction_agrees.astype(float)*(-np.log10(comparison.padj_external.clip(lower=1e-300))/10).clip(upper=1)*(comparison.log2FoldChange_external.abs()/2).clip(upper=1)
        np.testing.assert_allclose(expected.reindex(f.index),f.replication,equal_nan=True)
        mapping=pd.read_csv(ROOT/"data/annotations/reactome_v95_mouse.tsv",sep="\t")
        paths=pd.read_csv(ROOT/"results/GSE156496/deseq2/reactome_enrichment.csv")
        support={}
        for row in paths.query("direction == 'all' and padj < 0.05").itertuples():
            for gene in row.genes.split(";"):
                support[gene]=max(support.get(gene,0),min(-np.log10(max(row.padj,1e-300))/5,1))
        mapped=set(mapping.gene_id)
        np.testing.assert_allclose([support.get(g,0) if g in mapped else np.nan for g in f.index],f.pathway,equal_nan=True)
        loo=[]
        for wt in range(3):
            for case in range(3):
                ratio=np.log2((np.delete(values[:,3:],case,axis=1).mean(axis=1)+1)/(np.delete(values[:,:3],wt,axis=1).mean(axis=1)+1))
                loo.append((np.sign(ratio)==sign)&(np.abs(ratio)>1))
        np.testing.assert_allclose(np.asarray(loo).mean(axis=0),f.leave_pair_out_effect_stability)

    def test_string_raw_mapping_scores_and_all_metrics(self):
        folder=ROOT/"results/discovery/network"
        provenance=json.loads((folder/"provenance.json").read_text())
        for name,digest in provenance["sha256"].items():
            self.assertEqual(hashlib.sha256((folder/name).read_bytes()).hexdigest(),digest)
        mapping=pd.read_csv(folder/"mapping.csv")
        rawmap=json.loads((folder/"string_get_string_ids_raw.json").read_text())
        lookup={r["queryItem"]:r for r in rawmap}
        for row in mapping.itertuples():
            self.assertEqual(row.stringId,lookup[row.gene_id]["stringId"])
            self.assertEqual(lookup[row.gene_id]["ncbiTaxonId"],10090)
        raw={tuple(sorted([r["stringId_A"],r["stringId_B"]])):r for r in json.loads((folder/"string_network_raw.json").read_text())}
        edges=pd.read_csv(folder/"edges.csv")
        for row in edges.itertuples():
            source=raw[tuple(sorted([row.stringId_A,row.stringId_B]))]
            for key in ["score","nscore","fscore","pscore","ascore","escore","dscore","tscore"]:
                self.assertEqual(getattr(row,key),source[key])
        for threshold in (.4,.7,.9):
            graph=nx.Graph();graph.add_nodes_from(sorted(mapping.gene_id))
            graph.add_weighted_edges_from(edges.loc[edges.score>=threshold,["source","target","score"]].itertuples(index=False,name=None))
            saved=pd.read_csv(folder/f"nodes_{threshold}.csv").set_index("gene_id")
            for name,values in [("degree",dict(graph.degree())),("degree_centrality",nx.degree_centrality(graph)),
                                ("pagerank",nx.pagerank(graph,weight="weight")),
                                ("betweenness",nx.betweenness_centrality(graph,k=64,seed=156496,weight=None,normalized=True))]:
                np.testing.assert_allclose(pd.Series(values).reindex(saved.index),saved[name],rtol=1e-8,atol=1e-12)
            communities=sorted(nx.community.louvain_communities(graph,weight="weight",seed=156496),key=lambda c:(-len(c),min(c)))
            labels={g:i for i,group in enumerate(communities) for g in group}
            np.testing.assert_array_equal(pd.Series(labels).reindex(saved.index),saved.community)

    def test_new_reactome_backgrounds_and_full_BH_families(self):
        mapping=pd.read_csv(ROOT/"data/annotations/reactome_v95_mouse.tsv",sep="\t")
        for study in ("GSE156496","GSE132741","GSE284723"):
            name="deseq2_D51_vs_WT_unshrunken.csv" if study=="GSE156496" else "unshrunken.csv"
            de=pd.read_csv(ROOT/"results"/study/"deseq2"/name)
            universe=set(de.loc[de.padj.notna(),"gene_id"])&set(mapping.gene_id)
            paths=pd.read_csv(OUT/f"{study}_pathways.csv")
            for direction,f in paths.groupby("direction"):
                expected_terms=sum(10<=len(set(g.gene_id)&universe)<=500 for _,g in mapping.groupby("pathway_id"))
                self.assertEqual(len(f),expected_terms)
                self.assertTrue((f.universe_size==len(universe)).all())
                np.testing.assert_allclose(f.pvalue,hypergeom.sf(f.overlap-1,f.universe_size,f.pathway_size,f.selected_size),rtol=1e-8,atol=1e-15)
                np.testing.assert_allclose(f.padj,false_discovery_control(f.pvalue),rtol=1e-8,atol=1e-15)

    def test_third_raw_workbook_alignment_and_identifiers(self):
        raw=pd.read_excel(ROOT/"data/raw/GSE284723/GSE284723_rawCounts.xlsx",sheet_name="raw counts")
        raw=raw[~raw.EnsemblID.str.startswith("__")].copy()
        counts=pd.read_csv(ROOT/"data/processed/GSE284723/count_matrix.csv",index_col=0)
        self.assertEqual(len(raw),57010)
        self.assertTrue(counts.index.is_unique)
        self.assertTrue(counts.index.str.fullmatch(r"ENSMUSG\d+").all())
        np.testing.assert_array_equal(counts.index,raw.EnsemblID.str.replace(r"\.\d+$","",regex=True))
        np.testing.assert_array_equal(counts.to_numpy(),raw.drop(columns="EnsemblID").to_numpy())
        self.assertTrue((counts.to_numpy()>=0).all())
        self.assertTrue((counts.to_numpy()==np.floor(counts.to_numpy())).all())
        meta=pd.read_csv(ROOT/"data/processed/GSE284723/sample_metadata.csv")
        self.assertEqual(list(counts.columns),list(meta.count_column))
        self.assertEqual(meta.condition.value_counts().to_dict(),{"Control":5,"mKO":4})
        self.assertTrue(meta.accession.is_unique)
        review=json.loads((OUT/"geo_review/GSE284723.json").read_text())
        for row,sample in zip(meta.itertuples(),review["samples"]):
            self.assertEqual(row.accession,sample["accession"])
            self.assertEqual(row.genotype,sample["characteristics"]["genotype"])

    def test_third_filtering_BH_and_separate_shrinkage(self):
        counts=pd.read_csv(ROOT/"data/processed/GSE284723/count_matrix.csv",index_col=0)
        folder=ROOT/"results/GSE284723/deseq2"
        for name,threshold,minimum,expected in [("unshrunken",10,3,1817),("unshrunken_count20",20,3,1490),("unshrunken_minimum4",10,4,1669)]:
            f=pd.read_csv(folder/f"{name}.csv")
            self.assertEqual(set(f.gene_id),set(counts.index[(counts>=threshold).sum(axis=1)>=minimum]))
            self.assertEqual(int(((f.padj<.05)&(f.log2FoldChange.abs()>1)).sum()),expected)
            valid=f.dropna(subset=["padj"])
            np.testing.assert_allclose(valid.padj,false_discovery_control(valid.pvalue),rtol=1e-8,atol=1e-12)
            self.assertTrue((valid.lfcSE>0).all())
        original=pd.read_csv(folder/"unshrunken.csv")
        shrunk=pd.read_csv(folder/"apeglm.csv")
        np.testing.assert_array_equal(original.gene_id,shrunk.gene_id)
        np.testing.assert_allclose(original.padj,shrunk.padj,equal_nan=True)
        self.assertFalse(np.allclose(original.log2FoldChange,shrunk.log2FoldChange))

    def test_pairwise_overlap_and_log_probability(self):
        summary=pd.read_csv(OUT/"pairwise_summary.csv")
        for row in summary.itertuples():
            f=pd.read_csv(OUT/f"{row.study_a}_{row.study_b}_all_effects.csv").dropna(subset=["padj_a","padj_b"])
            a=(f.padj_a<.05)&(f.log2FoldChange_a.abs()>1)
            b=(f.padj_b<.05)&(f.log2FoldChange_b.abs()>1)
            self.assertEqual(len(f),row.universe)
            self.assertEqual(int((a&b).sum()),row.overlap)
            self.assertEqual(row.concordant+row.discordant,row.overlap)
            self.assertAlmostEqual(row.overlap_log10_p,hypergeom.logsf(row.overlap-1,len(f),int(a.sum()),int(b.sum()))/np.log(10),places=8)
        self.assertEqual(list(summary.overlap),[976,870,909])

    def test_selection_bias_and_fixed_universe(self):
        selection=pd.read_csv(OUT/"selection_audit.csv")
        for (_, _),f in selection.groupby(["study_a","study_b"]):
            all_genes=f[f.subset=="all_common_finite_effects"].iloc[0]
            intersection=f[f.subset=="DEG_intersection"].iloc[0]
            self.assertGreater(all_genes.genes,intersection.genes)
            self.assertLess(all_genes.sign_concordance,intersection.sign_concordance)
            fixed=f[f.subset=="scenario_fixed_valid_universe"]
            self.assertEqual(fixed.genes.nunique(),1)
        self.assertEqual(len(pd.read_csv(OUT/"statistical_sensitivity.csv")),108)

    def test_evidence_profiles_and_stability(self):
        f=pd.read_csv(OUT/"candidate_evidence.csv").set_index("gene_id")
        original=pd.read_csv(ROOT/"results/discovery/candidates/rankings.csv").set_index("gene_id")
        np.testing.assert_array_equal(f.rank_balanced,original.rank_balanced)
        np.testing.assert_allclose(f.score_balanced,original.score_balanced)
        mask=pd.Series(True,index=f.index)
        for study,scenarios in [("GSE156496",["unshrunken"]),("GSE132741",["unshrunken","unshrunken_no_replacement"]),("GSE284723",["unshrunken","unshrunken_count20","unshrunken_minimum4"])]:
            for scenario in scenarios:
                name="deseq2_D51_vs_WT_unshrunken" if study=="GSE156496" else scenario
                de=pd.read_csv(ROOT/"results"/study/"deseq2"/f"{name}.csv").set_index("gene_id").reindex(f.index)
                mask &= (de.padj<.05)&(de.log2FoldChange.abs()>1)&(np.sign(de.log2FoldChange)==np.sign(f.log2FoldChange))
            np.testing.assert_allclose(f[f"{study}_log2FoldChange"],de.log2FoldChange if study=="GSE156496" else pd.read_csv(ROOT/"results"/study/"deseq2/unshrunken.csv").set_index("gene_id").log2FoldChange.reindex(f.index),equal_nan=True)
        np.testing.assert_array_equal(mask,f.three_study_filter_outlier_stable)
        self.assertEqual(int(mask.sum()),572)

    def test_vector_figures_sources_and_hashes(self):
        manifest=json.loads((ROOT/"results/publication/figure_manifest.json").read_text())
        self.assertEqual(len(manifest),14)
        for figure in manifest:
            self.assertGreater(len(figure["caption"]),100)
            self.assertTrue(figure["parameters"])
            for name,digest in figure["files"].items():
                data=(ROOT/"results/publication"/name).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(),digest)
                if name.endswith(".svg"):
                    tree=ET.fromstring(data)
                    self.assertFalse(tree.findall(".//{http://www.w3.org/2000/svg}image"),"Vector figure must not contain rasterized layers")
                elif name.endswith(".pdf"):
                    self.assertTrue(data.startswith(b"%PDF"))
                elif name.endswith(".csv"):
                    self.assertGreater(len(pd.read_csv(ROOT/"results/publication"/name,low_memory=False)),0)

    def test_new_input_and_analysis_checksums_and_fit_audit(self):
        provenance=json.loads((ROOT/"data/processed/GSE284723/provenance.json").read_text())
        audit=json.loads((OUT/"audit.json").read_text())
        for hashes in [provenance["files"],audit["sha256"]]:
            for path,digest in hashes.items():
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
        self.assertEqual(audit["cohorts"][0]["age"],"1 month")
        fits=json.loads((OUT/"qc/fit_audit.json").read_text())
        for fit in fits.values():
            self.assertTrue(fit["reversal_verified"] and fit["BH_verified"] and fit["raw_counts_integer"])
            self.assertLess(fit["stored_fit_max_abs_difference"],1e-8)


class Phase4API(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.client=TestClient(app)

    def test_evidence_search_pagination_stable(self):
        response=self.client.get("/api/evidence");self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["total"],1499)
        self.assertEqual(len(response.json()["rows"]),25)
        other=self.client.get("/api/evidence?offset=25").json()
        self.assertNotEqual(other["rows"][0]["gene_id"],response.json()["rows"][0]["gene_id"])
        self.assertEqual(self.client.get("/api/evidence?stable=true").json()["total"],572)
        self.assertEqual(self.client.get("/api/evidence?q=ENSMUSG00000030789").json()["rows"][0]["gene_symbol"],"Itgax")
        self.assertEqual(self.client.get("/api/evidence?q=NOT_A_GENE").json()["total"],0)

    def test_compare_true_evidence_and_invalid_requests(self):
        response=self.client.get("/api/evidence/compare?genes=ENSMUSG00000030789")
        self.assertEqual(response.status_code,200)
        self.assertGreater(response.json()["rows"][0]["GSE284723_log2FoldChange"],0)
        self.assertEqual(self.client.get("/api/evidence/compare?genes=unknown").status_code,404)
        self.assertEqual(self.client.get("/api/evidence/compare?genes=a,b,c,d,e").status_code,422)
        self.assertEqual(self.client.get("/api/evidence/compare?genes=a,a").status_code,422)

    def test_sensitivity_actual_settings_and_query_validation(self):
        r=self.client.get("/api/statistical-sensitivity?fdr=0.05")
        self.assertEqual(r.status_code,200);self.assertEqual(len(r.json()),9)
        third=self.client.get("/api/statistical-sensitivity?study_b=GSE284723&fdr=0.01")
        self.assertEqual(third.status_code,200);self.assertEqual(len(third.json()),12)
        self.assertEqual(self.client.get("/api/statistical-sensitivity?fdr=0.03").status_code,422)

    def test_audit_and_corrected_metadata(self):
        r=self.client.get("/api/scientific-audit");self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json()["audit"]["cohorts"]),3)
        self.assertIn("1 month"," ".join(self.client.get("/api/replication").json()["heterogeneity"]))

    def test_publication_real_vector_downloads_and_traversal(self):
        r=self.client.get("/api/publication");self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json()),14)
        for figure in r.json():
            for name in figure["files"]:
                response=self.client.get("/api/publication/download/"+name)
                self.assertEqual(response.status_code,200)
                self.assertEqual(hashlib.sha256(response.content).hexdigest(),figure["files"][name])
        self.assertEqual(self.client.get("/api/publication/download/dds.rds").status_code,404)

    def test_publication_collection_and_research_documents(self):
        r=self.client.get("/api/publication/download/NeuroGene_Atlas_Publication_Figures.zip")
        self.assertEqual(r.status_code,200)
        with zipfile.ZipFile(io.BytesIO(r.content)) as archive:
            self.assertIsNone(archive.testzip())
            for figure in self.client.get("/api/publication").json():
                for name,digest in figure["files"].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(),digest)
        for artifact in ["evidence","sensitivity","audit","manuscript","provenance","pathways"]:
            response=self.client.get("/api/phase4/download/"+artifact)
            self.assertEqual(response.status_code,200)
            self.assertGreater(len(response.content),100)
