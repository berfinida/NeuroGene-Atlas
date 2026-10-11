"""Study-aware comparisons, selection audit and evidence profiles; no pooled model."""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, pearsonr, spearmanr

from scripts.discovery.evaluate_replication import enrich

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/phase4"
STUDIES = ("GSE156496", "GSE132741", "GSE284723")
COHORTS = [
    dict(accession=STUDIES[0], age="1 month", tissue="Tibialis anterior", case="D51 (exon 51 deletion)", reference="WT", samples=6, groups="3 WT / 3 D51", sex="Not reported in GEO sample fields", genome="mm10", independence="Six deposited libraries; individual animal IDs not provided in GEO", context="Constitutive dystrophin model; early disease", citation="https://pubmed.ncbi.nlm.nih.gov/33148801/"),
    dict(accession=STUDIES[1], age="30 weeks", tissue="Tibialis anterior", case="mdx", reference="WT", samples=15, groups="7 WT / 8 mdx", sex="Not reported in GEO sample fields", genome="mm10 symbol bridge", independence="15 unique animal identifiers in selected metadata", context="Selected age/tissue subset; fasting-duration and collection-time metadata available", citation="https://pubmed.ncbi.nlm.nih.gov/33751844/"),
    dict(accession=STUDIES[2], age="4-6 months", tissue="Tibialis anterior", case="Dmd flox52/Y: HSA mKO", reference="Dmd flox52/Y (not WT)", samples=9, groups="5 controls / 4 mKO", sex="Not explicitly reported in GEO; /Y genotype implies male but is not a sample sex field", genome="GRCm39 Gencode M32", independence="Nine distinct libraries; per-animal IDs not explicitly supplied. Design reports mice, not technical replicates", context="Conditional myofiber-specific deletion; nine deposited samples despite design claiming ten", citation="https://pmc.ncbi.nlm.nih.gov/articles/PMC12673120/"),
]


def load(study, name="unshrunken.csv"):
    if study == STUDIES[0] and name == "unshrunken.csv":
        name = "deseq2_D51_vs_WT_unshrunken.csv"
    f = pd.read_csv(ROOT / "results" / study / "deseq2" / name)
    assert not f.gene_id.duplicated().any()
    return f


def json_write(path, obj):
    # Scientific missingness stays null; NaN is not valid JSON.
    clean = json.loads(pd.Series([obj]).to_json(orient="values"))[0]
    path.write_text(json.dumps(clean, indent=2, allow_nan=False) + "\n")


def metrics(f, label):
    x, y = f.log2FoldChange_a, f.log2FoldChange_b
    p, q = float((x > 0).mean()), float((y > 0).mean())
    return dict(subset=label, genes=len(f), sign_concordance=float((np.sign(x) == np.sign(y)).mean()),
                marginal_sign_expectation=p*q+(1-p)*(1-q),
                pearson_r=float(pearsonr(x, y).statistic) if len(f)>2 else None,
                spearman_rho=float(spearmanr(x, y).statistic) if len(f)>2 else None,
                median_abs_lfc_difference=float((x-y).abs().median()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tables = {s: load(s) for s in STUDIES}
    mapping = pd.read_csv(ROOT / "data/annotations/reactome_v95_mouse.tsv", sep="\t")
    comparisons, selection, sensitivity = [], [], []
    pathway_tables = {}
    for s, f in tables.items():
        paths = enrich(f, mapping)
        paths.to_csv(OUT / f"{s}_pathways.csv", index=False)
        pathway_tables[s] = paths
    all_common = set.intersection(*(set(f.gene_id) for f in tables.values()))
    valid_common = set.intersection(*(set(f.loc[f.padj.notna(), "gene_id"]) for f in tables.values()))
    for a, b in itertools.combinations(STUDIES, 2):
        variants = {"default": tables[b]}
        if b == "GSE132741":
            variants["no_replacement"] = load(b, "unshrunken_no_replacement.csv")
            variants["fasting_adjusted"] = pd.read_csv(OUT/"unshrunken_fasting_adjusted.csv")
        if b == "GSE284723":
            for key in ("count20", "minimum4", "no_cooks"):
                variants[key] = load(b, f"unshrunken_{key}.csv")
            if a == "GSE132741":
                variants["external_fasting_adjusted"] = tables[b]
        base = tables[a].merge(tables[b], on="gene_id", suffixes=("_a", "_b"), validate="one_to_one")
        finite = base[np.isfinite(base.log2FoldChange_a) & np.isfinite(base.log2FoldChange_b)].copy()
        valid = finite.dropna(subset=["padj_a", "padj_b"]).copy()
        da = (valid.padj_a < .05) & (valid.log2FoldChange_a.abs() > 1)
        db = (valid.padj_b < .05) & (valid.log2FoldChange_b.abs() > 1)
        for label, f in [("all_common_finite_effects", finite), ("common_valid_FDR", valid),
                         ("study_a_selected", valid[da]), ("DEG_intersection", valid[da & db])]:
            selection.append(dict(study_a=a, study_b=b, **metrics(f, label)))
        finite.to_csv(OUT / f"{a}_{b}_all_effects.csv", index=False)
        fixed_ids = set(valid.gene_id)
        for other in variants.values():
            fixed_ids &= set(other.loc[other.padj.notna(), "gene_id"])
        if a == "GSE132741":
            context=pd.read_csv(OUT/"unshrunken_fasting_adjusted.csv")
            fixed_ids &= set(context.loc[context.padj.notna(),"gene_id"])
        for scenario, other in variants.items():
            left=context if scenario=="external_fasting_adjusted" else tables[a]
            joined = left.merge(other, on="gene_id", suffixes=("_a", "_b"), validate="one_to_one")
            joined = joined.dropna(subset=["padj_a", "padj_b"])
            for fdr in (.01, .05, .1):
                for lfc in (.5, 1, 1.5):
                    d = (joined.padj_a < fdr) & (joined.log2FoldChange_a.abs() > lfc)
                    e = (joined.padj_b < fdr) & (joined.log2FoldChange_b.abs() > lfc)
                    both = joined[d & e]
                    concordant = int((np.sign(both.log2FoldChange_a) == np.sign(both.log2FoldChange_b)).sum())
                    row = dict(study_a=a, study_b=b, scenario=scenario, fdr=fdr, lfc=lfc,
                               universe=len(joined), deg_a=int(d.sum()), deg_b=int(e.sum()), overlap=len(both),
                               concordant=concordant, discordant=len(both)-concordant,
                               jaccard=len(both)/int((d|e).sum()) if (d|e).any() else None,
                               overlap_log10_p=float(hypergeom.logsf(len(both)-1,len(joined),int(d.sum()),int(e.sum()))/np.log(10)))
                    sensitivity.append(row)
                    if scenario == "default" and fdr == .05 and lfc == 1:
                        comparisons.append(row)
            # The fixed intersection separates eligibility changes from effect/rank changes.
            fixed = joined[joined.gene_id.isin(fixed_ids)].copy()
            selection.append(dict(study_a=a,study_b=b,scenario=scenario,
                                  **metrics(fixed,"scenario_fixed_valid_universe")))
    pd.DataFrame(comparisons).to_csv(OUT / "pairwise_summary.csv", index=False)
    pd.DataFrame(selection).to_csv(OUT / "selection_audit.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(OUT / "statistical_sensitivity.csv", index=False)
    paths = []
    for a,b in itertools.combinations(STUDIES,2):
        merged = pathway_tables[a].merge(pathway_tables[b],on=["direction","pathway_id"],suffixes=("_a","_b"))
        merged["study_a"], merged["study_b"] = a,b
        paths.append(merged)
    pd.concat(paths).to_csv(OUT / "pathway_comparison.csv",index=False)
    # A common annotated background is a separate sensitivity analysis, never a replacement
    # for the study-specific enrichment inferential families.
    common_paths = []
    for s,f in tables.items():
        p = enrich(f[f.gene_id.isin(valid_common)],mapping)
        p["study"] = s
        common_paths.append(p)
    pd.concat(common_paths).to_csv(OUT / "pathways_common_background.csv",index=False)
    candidates = pd.read_csv(ROOT / "results/discovery/candidates/rankings.csv")
    nodes = pd.read_csv(ROOT / "results/discovery/network/nodes_0.7.csv").set_index("gene_id")
    evidence = candidates.copy().set_index("gene_id")
    direction = np.sign(evidence.log2FoldChange)
    robust = pd.Series(True,index=evidence.index)
    for s,f in tables.items():
        indexed=f.set_index("gene_id")
        for key in ("log2FoldChange","lfcSE","padj","baseMean"):
            evidence[f"{s}_{key}"] = indexed[key].reindex(evidence.index)
        shrink_name="deseq2_D51_vs_WT_apeglm.csv" if s==STUDIES[0] else "apeglm.csv"
        evidence[f"{s}_apeglm"] = load(s,shrink_name).set_index("gene_id").log2FoldChange.reindex(evidence.index)
        lfc=evidence[f"{s}_log2FoldChange"]
        evidence[f"{s}_direction_agrees"] = (np.sign(lfc)==direction).where(lfc.notna())
        deg=(evidence[f"{s}_padj"]<.05)&(lfc.abs()>1)&(np.sign(lfc)==direction)
        evidence[f"{s}_concordant_deg"]=deg
        robust &= deg
    for s,scenarios in [("GSE132741",["no_replacement"]),("GSE284723",["count20","minimum4"])]:
        for scenario in scenarios:
            f=load(s,f"unshrunken_{scenario}.csv").set_index("gene_id").reindex(evidence.index)
            stable=(f.padj<.05)&(f.log2FoldChange.abs()>1)&(np.sign(f.log2FoldChange)==direction)
            evidence[f"{s}_{scenario}_concordant_deg"]=stable
            robust &= stable
    evidence["three_study_filter_outlier_stable"] = robust
    context=pd.read_csv(OUT/"unshrunken_fasting_adjusted.csv").set_index("gene_id").reindex(evidence.index)
    context_stable=(context.padj<.05)&(context.log2FoldChange.abs()>1)&(np.sign(context.log2FoldChange)==direction)
    evidence["GSE132741_fasting_adjusted_log2fc"]=context.log2FoldChange
    evidence["GSE132741_fasting_adjusted_padj"]=context.padj
    evidence["three_study_context_filter_outlier_stable"]=robust&context_stable
    for key in ("degree","betweenness","pagerank","community"):
        if key in nodes:
            evidence[f"STRING_{key}"]=nodes[key].reindex(evidence.index)
    pathways={}
    for row in pathway_tables[STUDIES[0]].query("direction == 'all' and padj < 0.05").itertuples():
        for gene in str(row.genes).split(";"):
            pathways.setdefault(gene,[]).append(row.pathway_id)
    evidence["enriched_discovery_pathway_ids"]=[";".join(pathways.get(g,[])) for g in evidence.index]
    evidence.sort_values("rank_balanced").to_csv(OUT / "candidate_evidence.csv",na_rep="")
    files = [OUT/p for p in ["pairwise_summary.csv","selection_audit.csv","statistical_sensitivity.csv","candidate_evidence.csv","pathway_comparison.csv","pathways_common_background.csv"]]
    audit = dict(status="computed",clinical_validation=False,cohorts=COHORTS,comparisons=comparisons,
                 selection_audit=selection,common_tested_three_studies=len(all_common),common_valid_FDR_three_studies=len(valid_common),
                 stable_candidates=int(robust.sum()),candidate_ranking="Phase 3 rankings preserved. Third-study evidence is separate, not retrospectively added to the score.",
                 context_stable_candidates=int((robust&context_stable).sum()),
                 fasting_context=json.loads((OUT/"context_sensitivity.json").read_text()),
                 context_inference_coverage=dict(fasting_adjusted_valid_padj=int(pd.read_csv(OUT/"unshrunken_fasting_adjusted.csv").padj.notna().sum()),
                     unadjusted_no_replacement_valid_padj=int(load("GSE132741","unshrunken_no_replacement.csv").padj.notna().sum()),
                     automatic_outlier_filtering="DESeq2 automatic Cook filtering/replacement is not applied with a continuous covariate. Context sensitivity changes eligibility as well as estimates; not a pure deconfounding comparison."),
                 primary_age_correction="Original GSE156496 sample metadata states age: 1 month. Phase 3 age-unavailable wording was incorrect; numerical results unchanged.",
                 inference="Independent models/cohorts, not matched experimental conditions. No pooled effect or clinical inference.",
                 concordance_warning="DEG-intersection selection enriches strong shared effects; compare all common finite effects and marginal-sign expectation. Gene correlation and hypergeometric tests do not model inter-gene dependence.",
                 QC="No samples removed based on outcome. PCA is descriptive, not a test of sample independence or causal genotype effects.",
                 limitations=["Sex not explicitly documented in GEO sample fields; sex effects cannot be ruled out.","Genotype, age, conditional deletion, fasting context and genome annotation differ.","Third cohort has nine submitted libraries and no explicit individual-animal IDs; biological independence follows reported design, not independent verification.","Continuous fasting covariate disables automatic Cook filtering: adjusted/unadjusted no-replacement FDR coverage differs. Adjustment is diagnostic, not proof of confounder removal.","Counts reanalyzed, not raw FASTQ realignment. Reactome background excludes unmapped identifiers.","STRING edges are associations, not causal regulation; DEG selection biases connectivity.","Candidate weights are heuristic; correlated evidence and discovery selection prevent calibrated probability interpretation.","No meta-analysis: three heterogeneous model contexts, conditional-control comparator not WT, limited variance/cohort covariates.","Third-cohort publication already compares earlier dystrophin datasets; do not claim first biological discovery."],
                 reproduction=json.loads((ROOT/"results/validation/reproducibility.json").read_text()),
                 docker="Unavailable: docker executable not installed; container execution not tested",
                 sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    json_write(OUT/"audit.json",audit)
    print(json.dumps({"comparisons":comparisons,"stable_candidates":int(robust.sum())},indent=2))


if __name__ == "__main__":
    main()
