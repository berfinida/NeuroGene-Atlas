"""Build a standalone scientific report from stored outputs and observed validation."""
import base64
import html
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/reports'
def read(path):return json.loads((ROOT/path).read_text())
def esc(value):return html.escape(str(value))
def image(path,caption):
    data=base64.b64encode((ROOT/path).read_bytes()).decode()
    return f'<figure><img src="data:image/png;base64,{data}" alt="{esc(caption)}"><figcaption>{esc(caption)}</figcaption></figure>'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    primary=read('results/GSE156496/deseq2/summary.json')
    rep=read('results/discovery/replication/summary.json')
    methods=read('results/discovery/candidates/methods.json')
    reproduction=read('results/validation/reproducibility.json')
    validation_path=ROOT/'results/validation/final_validation.json'
    validation=json.loads(validation_path.read_text()) if validation_path.exists() else {'status':'Browser validation pending; no final pass claim'}
    rankings=pd.read_csv(ROOT/'results/discovery/candidates/rankings.csv')
    sensitivities=pd.read_csv(ROOT/'results/discovery/replication/sensitivity.csv')
    network=read('results/discovery/network/provenance.json')
    baseline=sensitivities[(sensitivities.outlier_setting=='no_replacement')&(sensitivities.fdr==.05)&(sensitivities.lfc==1)].iloc[0]
    paths=pd.read_csv(ROOT/'results/discovery/replication/pathway_comparison.csv')
    paths=paths[(paths.direction=='all')&paths.both_significant]
    sections=[f'''<h1>NeuroGene Atlas</h1><p class="subtitle">Phase 3 scientific validation and exploratory discovery report</p>
    <p><strong>Mouse transcriptomic replication is not clinical validation. Candidate rankings are hypothesis-generating, not validated biomarkers.</strong></p>
    <h2>Summary</h2><p>GSE156496: {primary['genes_tested']:,} tested genes, 1,499 DEGs (1,323 up, 176 down). GSE132741: 14,494 tested genes, 2,419 default DEGs; 2,019 with outlier replacement disabled.</p>
    <p>Across {rep['shared_inference_genes']:,} genes with valid inference in both cohorts: {rep['deg_overlap']} overlapping DEGs, {rep['direction_concordant_replicated_degs']} concordant and {rep['direction_discordant_replicated_degs']} discordant. Pearson r={rep['effect_pearson_r']:.6f}, Spearman rho={rep['effect_spearman_rho']:.6f}. DEG Jaccard={rep['deg_jaccard']:.6f}. {len(paths)} shared significant all-DEG Reactome pathways.</p>
    <h2>Datasets and Methods</h2><p>Discovery: mouse tibialis anterior, 3 WT and 3 Dmd exon-51 deletion samples (GSE156496), original mm10 featureCounts integer counts. External: 7 WT and 8 mdx exon-23 nonsense mice, GEO-labelled 30-week tibialis anterior (GSE132741); 15 unique animals. Blood, utrophin-altered genotypes and four younger TA samples excluded. GEO processing text mentions Cufflinks; supplied integer fragments-per-gene counts include HTSeq summary rows, and the primary article describes HTSeq-count.</p>
    <p>Exact, case-sensitive, unique symbol-to-Ensembl mapping against discovery mm10 annotations retained 23,414 of 24,451 external symbols; 1,037 unmapped/ambiguous entries excluded. No alias guessing, count rounding, or pooling.</p>
    <p>Separate DESeq2 designs ~condition, WT reference; positive unshrunken log2FC indicates higher mutant expression. Genes retained with at least 10 counts in at least 3 samples. Median-ratio normalization, parametric dispersion estimation, Wald tests, default Cook's cutoff and independent filtering; BH FDR adjustment. DEG definition: padj&lt;0.05 and |unshrunken log2FC|&gt;1, a post hoc effect cutoff, not a nonzero-null significance test. apeglm estimates exported separately with original inference retained. Discovery VST blind=FALSE; top-500-variable PCA, top-30-padj heatmap and Euclidean sample distances.</p>
    <p>External default minReplicatesForReplace=7 replaced counts in 1,243 genes. A second complete DESeq2 fit set minReplicatesForReplace=Inf. Cook's exclusions and valid-inference backgrounds differ between settings.</p>
    <h2>Cross-Dataset Results and Uncertainty</h2>''',
    image('results/reports/figures/effect_comparison.png','Unshrunken effects across shared inference genes; red marks discordant overlapping DEGs.'),
    f'''<p>Without external count replacement, shared inference is {int(baseline.shared_inference):,} genes and DEG overlap is {int(baseline.overlap)} ({int(baseline.concordant)} concordant; {int(baseline.discordant)} discordant). Effect Pearson r={rep['sensitivity'][9]['pearson_r']:.6f}. This change reflects both estimates and inference coverage, not a direct paired confidence interval.</p>
    <p>Across 18 threshold/outlier settings, overlap ranges {int(sensitivities.overlap.min())}-{int(sensitivities.overlap.max())}, concordance {sensitivities.concordance.min():.4%}-{sensitivities.concordance.max():.4%}. These perturbations measure robustness, not statistical uncertainty intervals. Genes and pathways are dependent; no gene-wise independence is assumed for uncertainty.</p>
    <ul>{''.join(f'<li>{esc(x)}</li>' for x in rep['heterogeneity'])}</ul>''',
    image('results/reports/figures/replication_sensitivity.png','FDR 0.01/0.05/0.1, absolute log2FC 0.5/1/1.5, with/without external replacement.'),
    '<h2>Functional Reproducibility</h2><p>Reactome release 95 mouse mapping. Each dataset uses its own valid-padj, Reactome-mapped background. Discovery background 6,893 of 14,358 eligible genes; terms of 10-500 background genes tested, including zero-overlap terms. One-sided hypergeometric ORA, BH separately over all/up/down tested families. Default shared all-DEG pathways: 30; replacement disabled: 33. Annotation overlap and bulk-tissue composition constrain interpretation.</p>',
    paths[['pathway_id','pathway_discovery','padj_discovery','padj_external']].to_html(index=False,escape=True,float_format=lambda v:f'{v:.3g}'),
    f'''<h2>STRING Association Network</h2><p>STRING {esc(network.get('string_version','12.0'))}, species 10090. 1,408 uniquely mapped discovery DEGs (of 1,499); 17,872 non-self undirected associations at confidence at least 0.4. At 0.7: 4,646 associations. No additional neighbor genes fetched. Associations are not necessarily physical interactions and do not establish causality; confidence is not effect strength.</p>
    <p>Metrics on full thresholded graph including isolates: degree, normalized degree, unweighted betweenness estimated using 64 seeded pivots, score-weighted PageRank, score-weighted Louvain communities with seed 156496. Display is capped at 200 nodes; exports retain the full graph. Evidence channels are combined, experiments, databases, coexpression, text mining, neighborhood, fusion and phylogenetic co-occurrence. Human/literature bias and DEG-induced selection affect network metrics.</p>
    <h2>Exploratory Candidate Prioritization</h2><p>{esc(methods['equation'])}. Balanced weights: significance 0.25, shrunken effect 0.20, sample-pair consistency 0.15, pathways 0.10, STRING degree 0.10, external directional evidence 0.20. Components capped in [0,1], so connectivity cannot exceed 10% of the balanced score.</p>
    <dl>{''.join(f'<dt>{esc(k)}</dt><dd>{esc(v)}</dd>' for k,v in methods['components'].items())}</dl><p>{esc(methods['missing_evidence'])}</p><p>{esc(methods['stability'])}</p><p>{esc(methods['limitations'])}</p>''',
    '<p>Scores are ordered descending with ascending Ensembl ID as a deterministic tie-break, not a biological preference. Display rounding can make distinct scores appear equal; full exported precision and rank-sensitivity ranges are authoritative.</p>',
    rankings[['rank_balanced','gene_symbol','gene_id','score_balanced','robust_replicated_deg','sensitivity_rank_min','sensitivity_rank_max']].head(20).to_html(index=False,escape=True,float_format=lambda v:f'{v:.4f}'),
    image('results/reports/figures/candidate_sensitivity.png','Rank and top-50 stability across eight weighting/network/outlier scenarios.'),
    f'''<h2>Reproducibility and Software</h2><p>Original discovery inputs and package versions verified. Independent raw-input reconstruction and R rerun matched all eight stored numeric tables, maximum absolute difference 0, with rtol=1e-8 and atol=1e-10. PDF timestamps and serialized R objects are not required to be byte-identical. External default and no-replacement fits completed, but a second isolated external raw-input rerun was not performed.</p>
    <pre>{esc(json.dumps(primary['package_versions'],indent=2))}</pre><p>Conda macOS ARM64 explicit lock and portable environment recipe supplied. Docker recipe provided but not built/tested; Docker unavailable. Source/results ZIPs include per-file SHA-256 manifests.</p>
    <h2>Observed Validation</h2><pre>{esc(json.dumps(validation,indent=2))}</pre>
    <h2>Limitations</h2><p>Small discovery cohort; unmatched genotype/age and independent experimental workflow; no batch covariate; only one independent mouse cohort; exact-symbol mapping excludes unresolved identifiers. Default external replacement is substantial and changes inference. ORA and network support are dependent on DEG selection and annotation. Scoring weights/caps are heuristic and sensitive; no human outcomes, clinical validation, or causal evidence. Browser testing covers Chromium desktop/mobile emulation, not Safari/Firefox or real assistive technology. No trained candidate classifier or calibrated biomarker probability.</p>
    <h2>References</h2><ol>
    <li><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156496">GEO GSE156496</a></li>
    <li><a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE132741">GEO GSE132741</a>; <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC8033515/">primary external-cohort study</a></li>
    <li><a href="https://doi.org/10.1186/s13059-014-0550-8">Love et al., DESeq2 (2014)</a></li>
    <li><a href="https://doi.org/10.1093/bioinformatics/bty895">Zhu et al., apeglm (2019)</a></li>
    <li><a href="https://download.reactome.org/95/Ensembl2Reactome.txt">Reactome 95 Ensembl mapping</a></li>
    <li><a href="https://string-db.org/help/api/">STRING API</a>; <a href="https://string-db.org/help/scores/">evidence scores</a></li>
    </ol><p>Full input/output hashes, session files, metadata and analysis parameters accompany the research bundle.</p>''']
    style='body{font:14px Arial,sans-serif;max-width:1050px;margin:40px auto;padding:0 24px;color:#243335;line-height:1.55}h1{font-size:34px}h2{font-size:21px;border-bottom:1px solid #ccd9d6;padding-bottom:8px;margin-top:32px}a{color:#148780}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;background:#f1f5f4;padding:16px}table{border-collapse:collapse;width:100%;font-size:10px}td,th{padding:6px;border-bottom:1px solid #dce5e4;text-align:left;overflow-wrap:anywhere}figure{margin:20px 0}img{max-width:100%;max-height:460px}figcaption{font-size:11px;color:#617274}dt{font-weight:bold}dd{margin-bottom:12px}.subtitle{color:#617274}@media print{body{margin:0;padding:0;font-size:10px}h2{break-after:avoid}figure,tr{break-inside:avoid}pre{font-size:8px}img{max-height:380px}a{color:inherit}}'
    output=OUT/'NeuroGene_Atlas_Scientific_Report.html'
    output.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>NeuroGene Atlas Scientific Report</title><style>'+style+'</style></head><body>'+''.join(sections)+'</body></html>')
    print(output)

if __name__=='__main__':main()
