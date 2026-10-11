"""Compare independent analyses in their shared inference universe without pooling counts."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, pearsonr, spearmanr
from scripts.rna_seq.reactome_enrichment import bh

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = ROOT / "results/GSE156496/deseq2"
EXTERNAL = ROOT / "results/GSE132741/deseq2"
OUT = ROOT / "results/discovery/replication"


def enrich(de,mapping):
    universe = set(de.loc[de.padj.notna(),"gene_id"]) & set(mapping.gene_id)
    deg = de[(de.padj<.05)&(de.log2FoldChange.abs()>1)]
    terms = []
    for direction in ["all","up","down"]:
        selected = deg if direction=="all" else deg[deg.log2FoldChange>0] if direction=="up" else deg[deg.log2FoldChange<0]
        selected_ids = set(selected.gene_id)&universe
        family = []
        for key,group in mapping.groupby("pathway_id"):
            genes = set(group.gene_id)&universe
            if not 10<=len(genes)<=500:
                continue
            overlap = genes&selected_ids
            family.append({"direction":direction,"pathway_id":key,"pathway":group.pathway.iloc[0],"overlap":len(overlap),
                           "universe_size":len(universe),"selected_size":len(selected_ids),"pathway_size":len(genes),
                           "pvalue":float(hypergeom.sf(len(overlap)-1,len(universe),len(genes),len(selected_ids))),"genes":";".join(sorted(overlap))})
        for row,padj in zip(family,bh([r["pvalue"] for r in family])):
            row["padj"]=float(padj)
        terms.extend(family)
    return pd.DataFrame(terms)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    discovery = pd.read_csv(PRIMARY / "deseq2_D51_vs_WT_unshrunken.csv")
    external = pd.read_csv(EXTERNAL / "unshrunken.csv")
    joined = discovery.merge(external,on="gene_id",suffixes=("_discovery","_external"),validate="one_to_one")
    shared = joined.dropna(subset=["padj_discovery","padj_external"]).copy()
    shared["discovery_deg"] = (shared.padj_discovery<.05)&(shared.log2FoldChange_discovery.abs()>1)
    shared["external_deg"] = (shared.padj_external<.05)&(shared.log2FoldChange_external.abs()>1)
    shared["direction_agrees"] = np.sign(shared.log2FoldChange_discovery)==np.sign(shared.log2FoldChange_external)
    shared["both_deg"] = shared.discovery_deg&shared.external_deg
    shared.to_csv(OUT / "gene_comparison.csv",index=False)
    no_replace = pd.read_csv(EXTERNAL / "unshrunken_no_replacement.csv")
    sensitivity = []
    for setting, other in [("default", external), ("no_replacement", no_replace)]:
        comparison = discovery.merge(other,on="gene_id",suffixes=("_discovery","_external"),validate="one_to_one").dropna(subset=["padj_discovery","padj_external"])
        comparison["direction_agrees"] = np.sign(comparison.log2FoldChange_discovery)==np.sign(comparison.log2FoldChange_external)
        comparison.to_csv(OUT / f"comparison_{setting}.csv",index=False)
        for fdr in [.01,.05,.1]:
            for lfc in [.5,1,1.5]:
                dmask=(comparison.padj_discovery<fdr)&(comparison.log2FoldChange_discovery.abs()>lfc)
                emask=(comparison.padj_external<fdr)&(comparison.log2FoldChange_external.abs()>lfc)
                both=comparison[dmask&emask]
                union=int((dmask|emask).sum())
                sensitivity.append({"outlier_setting":setting,"fdr":fdr,"lfc":lfc,"shared_inference":len(comparison),"discovery_degs":int(dmask.sum()),"external_degs":int(emask.sum()),"overlap":len(both),"concordant":int(both.direction_agrees.sum()),"discordant":int((~both.direction_agrees).sum()),"jaccard":len(both)/union if union else None,"concordance":float(both.direction_agrees.mean()) if len(both) else None,"pearson_r":float(pearsonr(comparison.log2FoldChange_discovery,comparison.log2FoldChange_external).statistic),"spearman_rho":float(spearmanr(comparison.log2FoldChange_discovery,comparison.log2FoldChange_external).statistic)})
    pd.DataFrame(sensitivity).to_csv(OUT / "sensitivity.csv",index=False)
    d = set(shared.loc[shared.discovery_deg,"gene_id"])
    e = set(shared.loc[shared.external_deg,"gene_id"])
    overlap = shared[shared.both_deg]
    mapping = pd.read_csv(ROOT / "data/annotations/reactome_v95_mouse.tsv",sep="\t")
    external_paths = enrich(external,mapping)
    external_paths.to_csv(EXTERNAL / "reactome_enrichment.csv",index=False)
    no_replace_paths = enrich(no_replace,mapping)
    no_replace_paths.to_csv(EXTERNAL / "reactome_no_replacement.csv",index=False)
    original_paths = pd.read_csv(PRIMARY / "reactome_enrichment.csv")
    path_comparison = original_paths.merge(external_paths,on=["pathway_id","direction"],suffixes=("_discovery","_external"),validate="one_to_one")
    path_comparison["both_significant"] = (path_comparison.padj_discovery<.05)&(path_comparison.padj_external<.05)
    path_comparison.to_csv(OUT / "pathway_comparison.csv",index=False)
    paths = {}
    for direction,table in path_comparison.groupby("direction"):
        sigd=set(table.loc[table.padj_discovery<.05,"pathway_id"])
        sige=set(table.loc[table.padj_external<.05,"pathway_id"])
        paths[direction]={"shared_tested_terms":len(table),"discovery_significant":len(sigd),"external_significant":len(sige),
                          "overlap":len(sigd&sige),"jaccard":len(sigd&sige)/len(sigd|sige) if sigd|sige else None}
    provenance=json.loads((ROOT / "data/processed/GSE132741/provenance.json").read_text())
    pearson=pearsonr(shared.log2FoldChange_discovery,shared.log2FoldChange_external)
    spearman=spearmanr(shared.log2FoldChange_discovery,shared.log2FoldChange_external)
    summary={"status":"complete", "discovery":"GSE156496", "independent":"GSE132741", "clinical_validation":False,
             "interpretation":"Independent cross-model transcriptomic replication in bulk mouse TA; genotype/age/workflow heterogeneity limits generalization",
             "shared_inference_genes":len(shared),"discovery_degs_in_shared_universe":len(d),"external_degs_in_shared_universe":len(e),
             "deg_overlap":len(d&e),"deg_jaccard":len(d&e)/len(d|e),
             "overlap_hypergeometric_pvalue":float(hypergeom.sf(len(d&e)-1,len(shared),len(d),len(e))),
             "direction_concordance_overlap":float(overlap.direction_agrees.mean()),
             "direction_concordant_replicated_degs":int(overlap.direction_agrees.sum()),
             "direction_discordant_replicated_degs":int((~overlap.direction_agrees).sum()),
             "direction_concordance_discovery_degs":float(shared.loc[shared.discovery_deg,"direction_agrees"].mean()),
             "effect_pearson_r":float(pearson.statistic),"effect_pearson_p":float(pearson.pvalue),
             "effect_spearman_rho":float(spearman.statistic),"effect_spearman_p":float(spearman.pvalue),
             "median_absolute_lfc_difference":float((shared.log2FoldChange_discovery-shared.log2FoldChange_external).abs().median()),
             "pathway_reproducibility":paths,"heterogeneity":provenance["heterogeneity"],"cohort":provenance,
             "external_summary":json.loads((EXTERNAL / "summary.json").read_text()),
             "pooling":"No pooling or meta-analysis; each dataset has its own DESeq2 normalization/design and Reactome background",
             "sensitivity":sensitivity,
             "sensitivity_interpretation":"18 perturbations: 3 FDR thresholds x 3 effect thresholds x default/no outlier replacement. Changing replacement also changes valid inference universes; these are not confidence intervals or independent experiments.",
             "no_replacement_shared_all_pathways":len(set(original_paths.loc[(original_paths.direction=='all')&(original_paths.padj<.05),'pathway_id']) & set(no_replace_paths.loc[(no_replace_paths.direction=='all')&(no_replace_paths.padj<.05),'pathway_id'])),
             "numerical_underflow":"P-values stored as 0 underflow floating point; interpret as below numerical precision, not exact zero.",
             "sources_reviewed":[{"accession":"GSE132741","decision":"Selected age-matched WT/mdx bulk TA subset","source":provenance["geo_url"]},
                                  {"accession":"GSE162455","decision":"Excluded: FDB/EDL/soleus; RPKM/ANOVA supplementary data, no raw count table","source":"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE162455"},
                                  {"accession":"GSE262341","decision":"Excluded: appropriate TA WT/mdx design but supplementary CPM rather than raw counts","source":"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE262341"}],
             "sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [EXTERNAL/"unshrunken.csv",EXTERNAL/"reactome_enrichment.csv",OUT/"gene_comparison.csv",OUT/"pathway_comparison.csv"]}}
    (OUT / "summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k not in {"cohort","sha256","external_summary"}},indent=2))


if __name__ == "__main__":
    main()
