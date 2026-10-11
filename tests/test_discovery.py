import hashlib
import io
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control, pearsonr, hypergeom
from fastapi.testclient import TestClient
from backend.main import app
from backend.discovery import graph_tables
from scripts.discovery.prioritize_candidates import weighted_score, PRESETS

ROOT=Path(__file__).resolve().parents[1]

class ResearchIntegrity(unittest.TestCase):
    def test_final_provenance_and_report_structure(self):
        provenance=json.loads((ROOT/'results/GSE156496/deseq2/provenance.json').read_text())
        for path,digest in provenance['sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
        from pypdf import PdfReader
        reader=PdfReader(ROOT/'results/reports/NeuroGene_Atlas_Scientific_Report.pdf')
        text=' '.join(page.extract_text() for page in reader.pages)
        self.assertGreaterEqual(len(reader.pages),3)
        self.assertIn('not clinical validation',text)
        self.assertIn('References',text)

    def test_external_inputs_and_sample_alignment(self):
        folder=ROOT/'data/processed/GSE132741'
        provenance=json.loads((folder/'provenance.json').read_text())
        for path,digest in provenance['sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
        counts=pd.read_csv(folder/'count_matrix.csv',index_col=0)
        meta=pd.read_csv(folder/'sample_metadata.csv')
        self.assertTrue(counts.index.is_unique)
        self.assertTrue(np.equal(counts.to_numpy(),np.floor(counts.to_numpy())).all())
        self.assertTrue((counts.to_numpy()>=0).all())
        self.assertEqual(set(counts.columns),set(meta.count_column))
        self.assertEqual(meta.condition.value_counts().to_dict(),{'mdx':8,'WT':7})
        bridge=pd.read_csv(folder/'symbol_bridge.csv')
        self.assertTrue(bridge.gene_id.is_unique)
        self.assertTrue(bridge.GeneName.is_unique)
        bridge=bridge.set_index('gene_id').loc[counts.index]
        for sample in meta.itertuples():
            raw=pd.read_csv(ROOT/'data/raw/GSE132741'/sample.filename,sep='\t',header=None,names=['GeneName','count']).set_index('GeneName')
            np.testing.assert_array_equal(counts[sample.count_column].to_numpy(),raw.loc[bridge.GeneName,'count'].to_numpy())
        self.assertTrue((meta.age_weeks==30).all())
        self.assertTrue(meta.mouse_id.is_unique)
        self.assertEqual(len(counts),23414)
        de=pd.read_csv(ROOT/'results/GSE132741/deseq2/unshrunken.csv')
        self.assertEqual(set(de.gene_id),set(counts.index[(counts>=10).sum(axis=1)>=3]))

    def test_external_statistics_and_outliers(self):
        folder=ROOT/'results/GSE132741/deseq2'
        default=pd.read_csv(folder/'unshrunken.csv')
        other=pd.read_csv(folder/'unshrunken_no_replacement.csv')
        self.assertEqual(len(default),14494)
        for frame,expected in [(default,2419),(other,2019)]:
            self.assertEqual(int(((frame.padj<.05)&(frame.log2FoldChange.abs()>1)).sum()),expected)
            tested=frame.dropna(subset=['padj'])
            np.testing.assert_allclose(tested.padj,false_discovery_control(tested.pvalue),rtol=1e-8,atol=1e-12)
        self.assertEqual(set(default.gene_id),set(other.gene_id))
        summary=json.loads((folder/'summary.json').read_text())
        self.assertEqual(summary['outlier_replaced_genes'],1243)
        self.assertEqual(int(pd.read_csv(folder/'outlier_replacement.csv').outlier_replaced.sum()),1243)

    def test_replication_recalculation(self):
        folder=ROOT/'results/discovery/replication'
        frame=pd.read_csv(folder/'gene_comparison.csv')
        summary=json.loads((folder/'summary.json').read_text())
        self.assertEqual(len(frame),summary['shared_inference_genes'])
        overlap=frame[frame.discovery_deg&frame.external_deg]
        self.assertEqual(len(overlap),976)
        self.assertEqual(int(overlap.direction_agrees.sum()),973)
        self.assertEqual(int((~overlap.direction_agrees).sum()),3)
        self.assertAlmostEqual(pearsonr(frame.log2FoldChange_discovery,frame.log2FoldChange_external).statistic,summary['effect_pearson_r'])
        sensitivity=pd.read_csv(folder/'sensitivity.csv')
        self.assertEqual(len(sensitivity),18)
        baseline=sensitivity[(sensitivity.outlier_setting=='no_replacement')&(sensitivity.fdr==.05)&(sensitivity.lfc==1)].iloc[0]
        self.assertEqual(baseline.overlap,896)
        self.assertFalse(summary['clinical_validation'])

    def test_external_pathway_background_and_bh(self):
        mapping=pd.read_csv(ROOT/'data/annotations/reactome_v95_mouse.tsv',sep='\t')
        for name,de_name in [('reactome_enrichment.csv','unshrunken.csv'),('reactome_no_replacement.csv','unshrunken_no_replacement.csv')]:
            de=pd.read_csv(ROOT/'results/GSE132741/deseq2'/de_name)
            universe=set(de.loc[de.padj.notna(),'gene_id'])&set(mapping.gene_id)
            paths=pd.read_csv(ROOT/'results/GSE132741/deseq2'/name)
            for direction,group in paths.groupby('direction'):
                selected=de[(de.padj<.05)&(de.log2FoldChange.abs()>1)]
                if direction!='all':selected=selected[selected.log2FoldChange>0] if direction=='up' else selected[selected.log2FoldChange<0]
                selected=set(selected.gene_id)&universe
                self.assertTrue((group.universe_size==len(universe)).all())
                self.assertTrue((group.selected_size==len(selected)).all())
                expected=hypergeom.sf(group.overlap-1,len(universe),group.pathway_size,len(selected))
                np.testing.assert_allclose(group.pvalue,expected,rtol=1e-8,atol=1e-15)
                np.testing.assert_allclose(group.padj,false_discovery_control(group.pvalue),rtol=1e-8,atol=1e-15)

    def test_string_metrics_and_evidence(self):
        edges=pd.read_csv(ROOT/'results/discovery/network/edges.csv')
        self.assertEqual(len(edges),17872)
        self.assertFalse((edges.source==edges.target).any())
        self.assertEqual(len({tuple(sorted((r.source,r.target))) for r in edges.itertuples()}),len(edges))
        for column in ['score','nscore','fscore','pscore','ascore','escore','dscore','tscore']:
            self.assertTrue(edges[column].between(0,1).all())
        nodes,selected=graph_tables(.7)
        self.assertEqual(len(nodes),1408)
        self.assertEqual(len(selected),4646)
        self.assertEqual(nodes.degree.sum(),2*len(selected))
        np.testing.assert_allclose(nodes.degree_centrality,nodes.degree/(len(nodes)-1))
        self.assertAlmostEqual(nodes.pagerank.sum(),1)

    def test_candidates_equations_missing_and_sensitivity(self):
        frame=pd.read_csv(ROOT/'results/discovery/candidates/rankings.csv')
        self.assertEqual(len(frame),1499)
        for name,weights in PRESETS.items():
            np.testing.assert_allclose(frame[f'score_{name}'],weighted_score(frame,weights),rtol=1e-10,atol=1e-12)
            self.assertTrue(frame[f'score_{name}'].between(0,1).all())
            self.assertEqual(set(frame[f'rank_{name}']),set(range(1,1500)))
        self.assertEqual(len(pd.read_csv(ROOT/'results/discovery/candidates/sensitivity.csv')),8)
        unknown=pd.DataFrame({'a':[1.0],'b':[np.nan]})
        self.assertEqual(weighted_score(unknown,{'a':.5,'b':.5}).iloc[0],.5)

class DiscoveryAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=TestClient(app)

    def test_network_search_and_full_downloads(self):
        response=self.client.get('/api/network').json()
        self.assertEqual(response['total_edges'],4646)
        self.assertEqual(len(response['nodes']),100)
        hits=self.client.get('/api/network?q=ENSMUSG00000030789').json()
        self.assertEqual(hits['nodes'][0]['gene_id'],'ENSMUSG00000030789')
        for table,count in [('nodes',1408),('edges',4646)]:
            response=self.client.get(f'/api/network/export/{table}')
            self.assertEqual(response.status_code,200)
            self.assertEqual(len(pd.read_csv(io.StringIO(response.text))),count)
        self.assertEqual(self.client.get('/api/network?confidence=.1').status_code,422)

    def test_replication_queries_and_pagination(self):
        self.assertEqual(self.client.get('/api/replication').json()['deg_overlap'],976)
        self.assertEqual(self.client.get('/api/replication/genes?subset=discordant').json()['total'],3)
        self.assertEqual(self.client.get('/api/replication/genes?outliers=no_replacement').json()['total'],896)
        self.assertEqual(len(self.client.get('/api/replication/pathways').json()),30)
        a=self.client.get('/api/replication/genes').json()['rows']
        b=self.client.get('/api/replication/genes?offset=50').json()['rows']
        self.assertFalse(set(r['gene_id'] for r in a)&set(r['gene_id'] for r in b))

    def test_candidate_presets_queries_and_downloads(self):
        for preset in PRESETS:
            response=self.client.get(f'/api/candidates?weighting={preset}').json()
            self.assertEqual(response['total'],1499)
            self.assertEqual(response['rows'][0][f'rank_{preset}'],1)
        self.assertEqual(self.client.get('/api/candidates?q=NO_SUCH_GENE').json()['total'],0)
        for artifact in ['candidates','sensitivity','replication','comparison','network_provenance','replication_sensitivity','pathway_comparison']:
            self.assertEqual(self.client.get(f'/api/discovery/download/{artifact}').status_code,200)

    def test_research_figures(self):
        for stem in ['effect_comparison','replication_sensitivity','candidate_sensitivity']:
            for ext,signature in [('png',b'\x89PNG'),('pdf',b'%PDF')]:
                response=self.client.get(f'/api/research/figures/{stem}.{ext}')
                self.assertEqual(response.status_code,200)
                self.assertTrue(response.content.startswith(signature))
