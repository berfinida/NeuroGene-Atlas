"""Transparent discovery ranking with explicit missing-evidence masks and sensitivity scenarios."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/discovery/candidates"
PRESETS = {
    "balanced": {"statistical":.25,"effect":.20,"consistency":.15,"pathway":.10,"network":.10,"replication":.20},
    "statistics": {"statistical":.40,"effect":.25,"consistency":.15,"pathway":.05,"network":.05,"replication":.10},
    "replication": {"statistical":.15,"effect":.15,"consistency":.10,"pathway":.05,"network":.05,"replication":.50},
    "no_network": {"statistical":.25,"effect":.20,"consistency":.15,"pathway":.10,"network":0,"replication":.20},
    "no_pathway": {"statistical":.25,"effect":.20,"consistency":.15,"pathway":0,"network":.10,"replication":.20},
}


def weighted_score(frame,weights):
    numerator = sum(frame[key].fillna(0)*weight for key,weight in weights.items())
    return numerator/sum(weights.values())


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    de = pd.read_csv(ROOT / "results/GSE156496/deseq2/deseq2_D51_vs_WT_unshrunken.csv")
    frame = de[(de.padj<.05)&(de.log2FoldChange.abs()>1)].copy().set_index("gene_id")
    shrunken = pd.read_csv(ROOT / "results/GSE156496/deseq2/deseq2_D51_vs_WT_apeglm.csv").set_index("gene_id")
    normalized = pd.read_csv(ROOT / "results/GSE156496/deseq2/normalized_counts.csv",index_col=0).loc[frame.index]
    values = normalized.to_numpy()
    signs = np.sign(frame.log2FoldChange.to_numpy())
    pairwise = np.sign(values[:,3:,None]-values[:,None,:3])
    frame["statistical"] = (-np.log10(frame.padj.clip(lower=1e-300))/20).clip(upper=1)
    frame["effect"] = (shrunken.loc[frame.index,"log2FoldChange"].abs()/3).clip(upper=1)
    frame["consistency"] = (pairwise==signs[:,None,None]).mean(axis=(1,2))
    loo = []
    for wt in range(3):
        for case in range(3):
            wt_mean = np.delete(values[:,:3],wt,axis=1).mean(axis=1)
            case_mean = np.delete(values[:,3:],case,axis=1).mean(axis=1)
            ratio = np.log2((case_mean+1)/(wt_mean+1))
            loo.append((np.sign(ratio)==signs)&(np.abs(ratio)>1))
    frame["leave_pair_out_effect_stability"] = np.asarray(loo).mean(axis=0)
    mapping = pd.read_csv(ROOT / "data/annotations/reactome_v95_mouse.tsv",sep="\t")
    paths = pd.read_csv(ROOT / "results/GSE156496/deseq2/reactome_enrichment.csv")
    paths = paths[(paths.direction=="all")&(paths.padj<.05)]
    support = {}
    for row in paths.itertuples():
        for gene in str(row.genes).split(";"):
            support[gene] = max(support.get(gene,0),min(-np.log10(max(row.padj,1e-300))/5,1))
    mapped = set(mapping.gene_id)
    frame["pathway"] = [support.get(gene,0) if gene in mapped else np.nan for gene in frame.index]
    nodes = pd.read_csv(ROOT / "results/discovery/network/nodes_0.7.csv").set_index("gene_id")
    max_degree = max(nodes.degree.max(),1)
    frame["network"] = frame.index.to_series().map((np.log1p(nodes.degree)/np.log1p(max_degree)).to_dict())
    compare = pd.read_csv(ROOT / "results/discovery/replication/gene_comparison.csv").set_index("gene_id")
    rep = compare.direction_agrees.astype(float)*(-np.log10(compare.padj_external.clip(lower=1e-300))/10).clip(upper=1)*(compare.log2FoldChange_external.abs()/2).clip(upper=1)
    frame["replication"] = frame.index.to_series().map(rep.to_dict())
    frame["external_log2fc"] = frame.index.to_series().map(compare.log2FoldChange_external.to_dict())
    frame["external_padj"] = frame.index.to_series().map(compare.padj_external.to_dict())
    frame["replicated_deg"] = frame.index.to_series().map((compare.external_deg&compare.direction_agrees).to_dict())
    frame["evidence_components_available"] = frame[list(PRESETS["balanced"])].notna().sum(axis=1)
    sensitivity = []
    for name,weights in PRESETS.items():
        frame[f"score_{name}"] = weighted_score(frame,weights)
        order = frame.sort_values([f"score_{name}","gene_id"],ascending=[False,True]).index
        rank = pd.Series(np.arange(1,len(frame)+1),index=order)
        frame[f"rank_{name}"] = rank
    from backend.discovery import graph_tables
    scenarios = list(PRESETS)
    for confidence in [.4,.9]:
        name=f"network_{int(confidence*100)}"
        graph_nodes,_=graph_tables(confidence)
        graph_nodes.to_csv(ROOT / f"results/discovery/network/nodes_{confidence}.csv",index=False)
        degrees=graph_nodes.set_index("gene_id").degree
        altered=frame.copy()
        altered["network"]=frame.index.to_series().map(np.log1p(degrees)/np.log1p(max(degrees.max(),1)))
        frame[f"score_{name}"]=weighted_score(altered,PRESETS["balanced"])
        order=frame.sort_values([f"score_{name}","gene_id"],ascending=[False,True]).index
        frame[f"rank_{name}"]=pd.Series(np.arange(1,len(frame)+1),index=order)
        scenarios.append(name)
    no_replace=pd.read_csv(ROOT / "results/discovery/replication/comparison_no_replacement.csv").set_index("gene_id")
    support_no_replace=no_replace.direction_agrees.astype(float)*(-np.log10(no_replace.padj_external.clip(lower=1e-300))/10).clip(upper=1)*(no_replace.log2FoldChange_external.abs()/2).clip(upper=1)
    altered=frame.copy()
    altered["replication"]=frame.index.to_series().map(support_no_replace)
    frame["replication_no_replacement"]=altered.replication
    frame["robust_replicated_deg"]=frame.replicated_deg.fillna(False)&frame.index.to_series().map((no_replace.direction_agrees&(no_replace.padj_external<.05)&(no_replace.log2FoldChange_external.abs()>1))).fillna(False)
    frame["score_no_replacement"]=weighted_score(altered,PRESETS["balanced"])
    order=frame.sort_values(["score_no_replacement","gene_id"],ascending=[False,True]).index
    frame["rank_no_replacement"]=pd.Series(np.arange(1,len(frame)+1),index=order)
    scenarios.append("no_replacement")
    reference = set(frame.nsmallest(50,"rank_balanced").index)
    for name in scenarios:
        chosen = set(frame.nsmallest(50,f"rank_{name}").index)
        sensitivity.append({"scenario":name,"top50_overlap_with_balanced":len(chosen&reference),
                            "rank_spearman_with_balanced":float(spearmanr(frame.rank_balanced,frame[f"rank_{name}"]).statistic)})
    ranks=frame[[f"rank_{name}" for name in scenarios]]
    frame["sensitivity_rank_min"] = ranks.min(axis=1)
    frame["sensitivity_rank_max"] = ranks.max(axis=1)
    frame["top50_scenario_fraction"] = (ranks<=50).mean(axis=1)
    frame.sort_values(["score_balanced","gene_id"],ascending=[False,True]).to_csv(OUT / "rankings.csv",na_rep="")
    pd.DataFrame(sensitivity).to_csv(OUT / "sensitivity.csv",index=False)
    methods={"status":"complete","clinical_status":"Hypothesis-generating candidates; not validated clinical biomarkers", "population":"All 1499 discovery DEGs",
             "equation":"score = sum(w_j * component_j * available_j) / sum(w_j)", "weights":PRESETS,
             "components":{"statistical":"min(-log10(discovery BH padj)/20,1)","effect":"min(abs(apeglm log2FC)/3,1)",
                           "consistency":"Fraction of 9 normalized D51-versus-WT sample pairs whose direction agrees with DESeq2",
                           "pathway":"Maximum min(-log10(pathway BH padj)/5,1) for all-DEG enriched Reactome terms containing the gene",
                           "network":"log(1+degree)/log(1+maximum degree), full STRING DEG-induced network at confidence 0.7",
                           "replication":"Direction agreement * min(-log10(external BH padj)/10,1) * min(abs(external unshrunken log2FC)/2,1)"},
             "missing_evidence":"Unmapped Reactome/STRING or missing external inference is NA and contributes no confirmed support; the denominator stays fixed. Missing does not mean negative biological evidence. Available-component count is exported.",
             "stability":"8 scenarios: 5 weight presets, STRING confidence 0.4/0.9, no external outlier replacement. Leave-one-WT/one-D51-pair-out effect stability uses 9 normalized-mean combinations, not repeated DESeq2 significance testing. DEG threshold sensitivity is reported separately for replication.",
             "limitations":"Weights and caps are explicit heuristics, not trained/calibrated probabilities. Components are dependent; pathway/network evidence has annotation and literature bias. Replication is one heterogeneous mouse cohort. Sensitivity is not independent validation.",
             "sensitivity":sensitivity}
    (OUT / "methods.json").write_text(json.dumps(methods,indent=2)+"\n")
    print(json.dumps({"ranked_genes":len(frame),"top_gene":frame.score_balanced.idxmax(),"sensitivity":sensitivity},indent=2))


if __name__ == "__main__":
    main()
