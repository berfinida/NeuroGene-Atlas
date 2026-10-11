"""Research documents from verified tables, with explicit observed-validation status."""
import base64
import html
import json
from pathlib import Path
import shutil
import zipfile

import markdown
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"results/phase4"
PUB=ROOT/"results/publication"


def table(frame):
    lines=["| "+" | ".join(frame.columns)+" |","| "+" | ".join(["---"]*len(frame.columns))+" |"]
    for row in frame.itertuples(index=False,name=None):
        lines.append("| "+" | ".join(f"{v:.6g}" if isinstance(v,float) else str(v).replace("|","/") for v in row)+" |")
    return "\n".join(lines)


def main():
    audit=json.loads((OUT/"audit.json").read_text())
    fits=json.loads((OUT/"qc/fit_audit.json").read_text())
    third=json.loads((ROOT/"results/GSE284723/deseq2/summary.json").read_text())
    methods=json.loads((ROOT/"results/discovery/candidates/methods.json").read_text())
    selected=pd.read_csv(OUT/"selection_audit.csv")
    sensitivity=pd.read_csv(OUT/"statistical_sensitivity.csv")
    pairwise=pd.read_csv(OUT/"pairwise_summary.csv")
    paths=pd.read_csv(OUT/"pathway_comparison.csv")
    pathway_counts=[]
    for (a,b),p in paths[paths.direction=="all"].groupby(["study_a","study_b"]):
        pathway_counts.append(dict(study_a=a,study_b=b,shared_tested_terms=len(p),shared_enriched_terms=int(((p.padj_a<.05)&(p.padj_b<.05)).sum())))
    cohort_table=table(pd.DataFrame(audit["cohorts"])[["accession","age","groups","case","reference","genome"]])
    pair_table=table(pairwise[["study_a","study_b","universe","overlap","concordant","discordant","overlap_log10_p"]])
    bias_table=table(selected[selected.subset.isin(["all_common_finite_effects","DEG_intersection"])][["study_a","study_b","subset","genes","sign_concordance","marginal_sign_expectation","pearson_r","spearman_rho"]])
    path_table=table(pd.DataFrame(pathway_counts))
    summary=f"Discovery tested 14,359 genes and identified 1,499 DEGs. GSE132741 tested 14,494 genes (2,419 default DEGs; 2,019 without replacement). GSE284723 tested 15,009 genes and identified 1,817 DEGs. Discovery overlaps were 976 with mdx and 870 with conditional mKO, including 973 and 868 concordant directions. Across three default fits, external replacement disabled and both third-study count-filter alternatives, {audit['stable_candidates']} discovery candidates were concordant DEGs; {audit['context_stable_candidates']} also retained support after measured fasting-duration adjustment. These are exploratory mouse findings, not clinical validation."
    references="""1. [GEO GSE156496](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156496); [Degenerative and regenerative pathways underlying Duchenne muscular dystrophy revealed by single-nucleus RNA sequencing](https://pubmed.ncbi.nlm.nih.gov/33148801/). This reanalysis uses deposited bulk-muscle counts.
2. [GEO GSE132741](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE132741); [Peripheral blood transcriptome profiling enables monitoring disease progression in dystrophic mice and patients](https://pubmed.ncbi.nlm.nih.gov/33751844/). Only the mouse TA subset is analyzed here.
3. [GEO GSE284723](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE284723); [Karuppasamy et al. Conditional Dmd ablation in muscle and brain causes profound effects on muscle function and neurobehavior. Communications Biology (2025)](https://doi.org/10.1038/s42003-025-09128-y).
4. [Love, Huber and Anders. Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. Genome Biology (2014)](https://doi.org/10.1186/s13059-014-0550-8).
5. [Zhu, Ibrahim and Love. Heavy-tailed prior distributions for sequence count data: removing the noise and preserving large differences. Bioinformatics](https://doi.org/10.1093/bioinformatics/bty895).
6. [Reactome release 95 Ensembl mapping](https://download.reactome.org/95/Ensembl2Reactome.txt). Release-pinned mouse subset and original source hashes are bundled.
7. [STRING database in 2023: protein-protein association networks and functional enrichment analyses for any sequenced genome of interest](https://pubmed.ncbi.nlm.nih.gov/36370105/); [official score documentation](https://string-db.org/help/scores/).
8. Reviewed exclusions: [GSE126416](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE126416), [GSE262341](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE262341), [GSE324363](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE324363). Cached official matrices accompany the evidence review.
9. [Official DESeq2 vignette, count-outlier handling](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html). Continuous-covariate behavior also verified in the installed DESeq2 1.46.0 vignette.
"""
    limitations="\n".join(f"- {x}" for x in audit["limitations"])
    fit_checks="\n".join(f"- {s}: {v['genes']:,} fitted genes, {v['samples']} libraries; integer fitted counts, reverse contrast and BH verified. Stored log2FC maximum absolute difference {v['stored_fit_max_abs_difference']:.3g}." for s,v in fits.items())
    formal=f"""# Scientific Audit Report

## Scope and Evidence

Phase 4 audit of supplied count matrices, original GEO sample fields, DESeq2 objects, cross-model comparisons, Reactome v95, cached STRING v12.0 and exploratory rankings. Evidence is under `results/phase4/` and `data/raw/`. No FASTQ realignment, new wet-lab experiments or patient outcomes were analyzed.

## Required Corrections

1. **Corrected:** Original GSE156496 sample fields report one-month age, not unavailable. Current methods/limitations/API interpretation corrected; historical Phase 3 artifacts and numerical results retained.
2. **Unresolved:** Third-study GEO design says five mice/group, but nine libraries are deposited (five controls/four mKO). The publication figure legend describes four/group. All nine deposited libraries were used; no control was removed without a verified exclusion reason. These outputs need not match published DEG counts.
3. **Unresolved:** Third-study design prose says expected counts/FPKM, but processing specifies HTSeq-count and workbook values are integers. GSE132741 GEO processing mentions Cufflinks while supplied files are integer HTSeq-format counts. No counts were rounded or replaced by FPKM.
4. **Unknown:** Sex is not explicit in these GEO sample fields. The third /Y genotype suggests male, but is not a sample sex annotation. Individual animal IDs are explicit for fifteen selected external animals, not discovery/third libraries. Library uniqueness is not independent verification of animal uniqueness.
5. **Nomenclature caution:** Third-study article describes its previous CRISPR comparison as exon 52, whereas discovery GEO labels specify exon 51. Retain deposited contrasts; do not silently reassign genotype to agree with the article.

## Sample Metadata and Study Design

{cohort_table}

Original fields, including genotype and fasting times, are exported in `original_sample_metadata.json`. External fasting intervals are 274-435 min (WT; mean 339.43) and 275-390 min (mdx; mean 321.875). Fifteen unique animal IDs are verified. Exploratory context model: `~fasting_hours_centered+condition`, count replacement disabled. Clock times interpreted as same-day collection; fasting may be a mediator or proxy, not necessarily an appropriate causal covariate. No outcome-driven sample exclusions or cross-study count pooling.

## Identifier and Input Integrity

Primary input hashes and sample ordering are verified. External exact case-sensitive, unique symbol-to-Ensembl bridge retains 23,414/24,451 symbols (1,037 unresolved/ambiguous excluded), without alias guessing. Third workbook contains 57,010 gene rows plus five HTSeq summary rows. Summary rows are excluded and separately exported. Only Ensembl version suffixes are removed; duplicate stable IDs prohibited. All nine gene-count columns are nonnegative integers, aligned by GEO title/accession/genotype. Stable IDs do not remove GRCm39/M32 versus mm10 counting-definition differences. Input/output SHA-256 files are bundled.

## DESeq2 and QC Verification

{fit_checks}

Separate control-reference `~condition` fits, median-ratio size factors, parametric dispersions, Wald tests, BH and independent filtering at alpha=0.05. DEGs require padj<0.05 and |unshrunken log2FC|>1: post hoc effect selection, not a nonzero-null significance test. apeglm effects remain separate from original p-values. R 4.4.3, DESeq2 1.46.0, apeglm 1.28.0 and jsonlite 2.0.0.

Default external replacement affects 1,243 genes; a complete no-replacement fit exists. Third groups 5/4 do not meet default replacement eligibility (7). Five third-study genes have Cook-excluded p-values; disabling Cook exclusion is diagnostic only. PCA is recomputed from stored fitted objects using VST blind=False, top 500 variable genes; percentages/distances are exported. Per-library retained-gene count totals, size factors, median/max Cook values are in `qc/*_samples.csv`; these totals are not total sequenced reads. PCA cannot certify animal independence, eliminate cell-mixture/batch confounding or prove causality. No sample was excluded for improving results.

**Continuous-covariate caveat:** DESeq2 does not automatically filter/replace Cook outliers for continuous designs [9]. Fasting-adjusted inference has {audit['context_inference_coverage']['fasting_adjusted_valid_padj']:,} valid adjusted p-values versus {audit['context_inference_coverage']['unadjusted_no_replacement_valid_padj']:,} in the unadjusted no-replacement fit. Therefore 2,958 adjusted DEGs versus 2,019 unadjusted no-replacement DEGs reflects changed outlier eligibility as well as model estimates. The adjusted discovery overlap is 974 (956 concordant, 18 discordant). It is diagnostic, not a clean causal measure of fasting confounding. Fixed-universe comparisons are exported; the 555 context-supported candidates are already required to pass unadjusted Cook-filtered no-replacement criteria.

## Concordance and Selection Bias

{bias_table}

Discovery/mdx sign agreement rises from 75.29% across all finite common effects to 99.69% in overlapping DEGs, approximately 24.4 percentage points of selection-associated increase. Its DEG-intersection marginal sign expectation is 86.25%, versus approximately 50% across all common genes. Strong shared injury/regeneration/immune responses are plausible; selecting two significant large effects and bulk composition changes also raise agreement. These sources cannot be apportioned causally by this analysis. Marginal expectation is descriptive, not a valid dependent-gene null test. All-gene correlations and a fixed eligible universe across setting alternatives are provided to expose, not erase, selection effects.

## Overlap, Pathways and Sensitivity

{pair_table}

Hypergeometric log-survival values avoid numerical zero probabilities. Pair-specific common nonmissing-FDR genes define the universe, not all mouse genes. Exchangeability assumptions omit correlated genes and downstream exploratory multiplicity. No pooled effect or meta-analysis is justified by the available heterogeneous contexts.

{path_table}

Reactome v95 uses separately mapped valid-FDR backgrounds. All terms with 10-500 background genes, including zero-overlap terms, enter one-sided hypergeometric/BH families separately for all/up/down. Common-three-study-background enrichment is a separate sensitivity analysis. Coverage and universe sizes are exported.

There are {len(sensitivity)} threshold/context/outlier/filter setting rows across three study pairs; overlap ranges {int(sensitivity.overlap.min())}-{int(sensitivity.overlap.max())} across different universes, not a confidence interval. Third filtering >=20 in >=3 yields 1,490 DEGs; >=10 in >=4 yields 1,669, versus default 1,817. Fasting-adjusted external fit yields {audit['fasting_context']['DEGs']} DEGs without replacement. Discovery/mdx overlap falls 976 to 896 with replacement disabled. {audit['stable_candidates']} candidates pass all specified three-study/default/no-replacement/third-filter criteria; {audit['context_stable_candidates']} also pass context adjustment. No new primary filtering refit grid; leave-pair-out expression perturbations do not substitute for significance refits.

## STRING Association Network

Mouse taxon 10090, STRING v12.0: 1,408 uniquely mapped discovery DEGs of 1,499; 17,872 unique undirected non-self associations >=0.4; 4,646 associations >=0.7. Endpoints, scores, seven evidence channels, raw hashes, degree handshake and normalized PageRank are checked by integrity tests. Degree normalization uses n-1. Unweighted betweenness approximates 64 seeded pivots; PageRank and Louvain use confidence weights, with seed 156496. Isolates remain in full graphs. Communities are algorithm-dependent, not independently measured biology. Cached versioned responses, not live updated predictions, are the source; no additional neighbor genes. Display-selected hubs and DEG-induced graphs cannot establish disease specificity. Associations are not causality or necessarily physical binding.

## Candidate Formula Audit

Equation: `{methods['equation']}`. Balanced weights: statistical .25, effect .20, consistency .15, pathway .10, network .10, replication .20. Missing components stay NA and contribute zero with a fixed preset denominator. Connectivity cannot exceed 10% in balanced scoring; omission presets renormalize by their own fixed weight sum.

"""+"\n".join(f"- {key}: {value}" for key,value in methods["components"].items())+f"""

Nine pairwise normalized sample comparisons and nine leave-pair-out mean-ratio perturbations (+1 pseudocount) are descriptive, not independently repeated experiments. First three columns must be WT and last three D51, checked against metadata in tests. Five presets, two network thresholds and no-replacement setting give eight rank scenarios. Ties use gene ID, not a biological preference. Third-study evidence is separate from preserved scores, preventing retrospective score inflation. Evidence includes effects, SE, FDR, sign, pathways, centrality and sensitivity for every discovery candidate. Correlated heuristic evidence is not calibrated probability.

## Reproduction and Software Status

Prior Phase 3 isolated raw-input discovery rerun matched eight numeric tables exactly (rtol=1e-8, atol=1e-10); record preserved and input hashes rechecked. Current fitted objects reproduce log2FC within 5.33e-15 and verify reverse contrasts/BH. Third default and two filter fits and external fasting-context fit executed. External studies have not been independently reproduced in a second environment. Docker executable absent, recipe untested. Clean-extraction tests verify software/artifacts, not independent experimental replication. Actual current software outcomes are recorded separately in `results/validation/final_validation.json`; do not substitute Phase 3 outcomes for Phase 4 validation.

## Limitations

{limitations}

## References

{references}
"""
    (ROOT/"SCIENTIFIC_AUDIT_REPORT.md").write_text(formal)
    manuscript=f"""# Study-Aware Reanalysis of Dystrophin-Deficient Mouse Muscle: Cross-Model Evidence, Selection Bias and Exploratory Candidate Prioritization

Manuscript draft for author review. Computational reanalysis only; author list, affiliations, contributions, funding and ethics declarations require investigator confirmation. No new experiments were performed.

## Structured Abstract

### Background
Public mouse-muscle transcriptomes can assess reproducibility of dystrophin-loss responses, but highly concordant selected genes may conceal selection bias and heterogeneous model contexts.

### Methods
Three deposited integer-count datasets were analyzed using separate DESeq2 models. Unique identifiers harmonized genes without pooling counts. Concordance was evaluated over all commonly tested finite effects and DEG intersections. Reactome and STRING provided contextual evidence. Thresholds, outlier handling, count filtering, measured fasting duration and scoring weights were perturbed; candidate evidence was separated from ranking.

### Results
{summary} Discovery-mdx agreement was 75.3% across all common finite effects but 99.7% among overlapping DEGs; discovery-conditional agreement was 70.7% versus 99.8%.

### Conclusions
The platform supports auditable, exploratory cross-model mouse research. Shared effects and heuristic candidate stability are not equivalent to causal mechanism, human diagnostic discrimination or therapeutic validation.

## Introduction

Dystrophin deficiency disrupts muscle homeostasis across distinct models. GSE156496, GSE132741 and GSE284723 differ in genotype, age and processing [1-3]. Bulk muscle data cannot distinguish cell-intrinsic effects from changing immune, stromal or regenerating-cell proportions without additional analysis. Study-aware comparisons should therefore quantify common expression patterns while retaining their biological context.

NeuroGene Atlas is a reproducible evidence platform, not a trained biomarker predictor. This work asks whether effects agree beyond selected DEG intersections, how analytical choices change overlap, and which discovery candidates retain support across mouse models. The conditional-model publication already compares cytokine/extracellular-matrix signals with earlier dystrophin data [3]; we claim transparent reanalysis and robustness assessment, not first discovery of those processes.

## Materials and Methods

### Cohort Selection

{cohort_table}

GSE132741 was restricted to GEO-labelled 30-week WT/mdx TA, with fifteen unique mouse IDs. Blood, other genotypes and younger muscle samples were excluded using metadata, not observed concordance. GSE284723 contains five floxed controls and four conditional myofiber-knockout libraries. Floxed controls are not WT. Nine libraries were retained despite a ten-mouse design statement and a four-per-group published figure legend; no unsupported exclusion was introduced. Discovery age was corrected to one month from all six original GEO sample fields. Explicit sex and per-animal identity are incomplete; distinct libraries do not independently establish distinct animals.

GSE126416 was excluded as an individual-animal replication: quadriceps RNA is pooled into three WT and three mdx libraries, with supplied Cufflinks-derived expression rather than verified integer counts. GSE262341 provides CPM/DEG tables, not a verified raw matrix. GSE324363 is a treatment comparison within dystrophic mice, not disease versus healthy controls. These decisions are supported by cached official matrices [8]. Raw-read reconstruction is future work, not completed validation.

### Counts and Differential Expression

Original counts were checked for nonnegative integers, unique identifiers and metadata alignment. External symbols were bridged using exact, unique discovery annotations, excluding 1,037 unresolved/ambiguous entries. Third Ensembl versions were stripped without aliases/aggregation; five HTSeq summary rows excluded. Counting definitions differ between mm10 and GRCm39/M32, even for stable identifiers.

Separate DESeq2 models [4] used `~condition`, own control reference, median-ratio normalization, parametric dispersion and Wald inference. Default filtering retained >=10 counts in >=3 libraries. BH adjustment and independent filtering used alpha=0.05; DEGs required padj<0.05 and |unshrunken log2FC|>1. This is post hoc effect selection rather than a thresholded-null test. apeglm estimates [5] were exported separately without replacing original p-values.

External default replacement was compared with a full no-replacement fit. Discovery and third groups are below replacement eligibility. Third alternatives retain >=20 counts in >=3 libraries or >=10 in >=4. Cook-cutoff-disabled results are diagnostic only. A separate external `~fasting_hours_centered+condition` model without replacement examined measured context, assuming same-day clock times. Fasting may be a mediator or proxy; this is not guaranteed causal deconfounding. PCA used VST blind=False and 500 highest-variance features without outcome-driven sample removal.

### Cross-Study and Functional Analysis

Unshrunken effects were compared over all common finite effects, common valid-FDR genes, study-A DEGs and DEG intersections. Pearson/Spearman correlations, sign agreement, Jaccard overlap and descriptive hypergeometric log-survival values were computed. Pair-specific common nonmissing-FDR genes define overlap universes. A fixed valid-FDR universe across each set of alternatives separates eligibility changes from effect changes. Descriptive marginal-sign expectation is p_A*p_B+(1-p_A)*(1-p_B), not an independent-gene null test. Heterogeneous genotypes, controls and incomplete covariates do not justify pooling or meta-analysis.

Reactome v95 [6] uses separate mapped valid-FDR backgrounds, terms containing 10-500 background genes, one-sided over-representation tests and BH over all tested terms per direction, including zero overlaps. Fixed common-background enrichment is sensitivity evidence. Cached STRING v12.0 [7] supplies mouse functional associations and component confidence scores. Metrics retain isolates: degree, normalized degree, 64-pivot approximate betweenness, weighted PageRank and seeded weighted Louvain. These are associations, not causal regulation.

### Candidate Evidence and Reproducibility

The original 1,499 candidate ranks were preserved. Scores combine bounded significance, shrunken effect, sample-pair consistency, pathway support, STRING degree and external directional evidence, with balanced weights .25/.20/.15/.10/.10/.20. Missing evidence supplies no confirmed support under a fixed denominator. Heuristic weights, caps and dependent components prevent calibrated probability interpretation. Eight weight/network/outlier settings provide rank ranges and top-50 stability. Third-study effect, SE, FDR and direction are separate evidence, not retrospectively inserted into scores.

Stable candidates are concordant DEGs across three default fits, external no replacement and both third count filters. Fasting-adjustment stability is separately reported. Approximate unshrunken Wald intervals are displayed per study, with no pooled effect. Source counts, sessions, commands, SHA manifests, vector figures and source CSVs accompany the release. Stored-object contrasts/BH were recalculated; prior isolated discovery reproduction was preserved. External second-environment reproduction and FASTQ realignment were not performed. Software tests verify functionality and integrity, not biological validity.

## Results

### Differential Expression and Audit

{summary} Third filter alternatives yielded 1,490 and 1,669 DEGs; the fasting-adjusted external model yielded {audit['fasting_context']['DEGs']} DEGs without replacement. Stored log2FC recomputation differences were at most 5.33e-15. Deposited/published third-sample discrepancies remain explicit; published DEG counts are not expected to be reproduced by arbitrarily dropping one control.

### Concordance and Selection

{pair_table}

{bias_table}

Discovery-mdx overlap decreases to 896 with replacement disabled. All-gene Pearson correlations are 0.765 (discovery-mdx), 0.761 (discovery-conditional) and 0.659 (mdx-conditional); Spearman values are 0.685, 0.619 and 0.512. Agreement is much higher after selecting significant intersections, which also have skewed sign marginals. Thus 973/976 concordance is not an unbiased genome-wide replication rate, although broad correlations support shared expression patterns.

### Functional and Candidate Evidence

{path_table}

Shared enriched terms use separate inferential backgrounds; common-background sensitivity exposes annotation dependence. STRING retains 1,408 genes and 17,872 associations >=0.4; 4,646 associations remain >=0.7. High-degree display selection cannot establish pathogenicity. Preserved top candidates include Itgax, Tyrobp, Itgb2, Cd68 and Trem2; forest plots show separate approximate Wald intervals. Candidate stability remains conditional on discovery selection and chosen cutoffs.

## Discussion

Distinct dystrophin-deficient models exhibit correlated muscle effects, but near-complete selected-DEG agreement is partly a property of selection. Comparing approximately 66-75% all-gene sign agreement with approximately 98-100% intersection agreement demonstrates why the tested universe must accompany replication claims. Shared injury and immune/regenerative responses are plausible, but bulk composition and unmeasured covariates can generate similar patterns. No cell-intrinsic or causal attribution follows from these comparisons.

Outlier replacement and filtering materially affect counts and overlap. Fixed-universe correlations help distinguish eligibility changes, but missingness is not random and perturbations are not uncertainty intervals. Fasting adjustment is a measured-context diagnostic, not proof that an adjusted genotype effect is biologically preferable. Collection-time effects and batch covariates remain incompletely modeled; fasting could reflect genotype-associated physiology. Stable Ensembl identifiers reduce ambiguity but do not reconcile genome annotations or upstream quantification.

DESeq2's continuous-covariate design does not apply automatic Cook filtering [9]. All 14,494 context-fit genes have valid FDR versus 13,252 in the unadjusted no-replacement fit. The 2,958/2,019 DEG comparison consequently mixes eligibility and effect changes, not solely fasting adjustment. The 555 context-supported candidates already pass the unadjusted no-replacement filter; this does not confer causal or clinical validity.

Candidate profiles prioritize inspectability over prediction. Capping network evidence limits hub dominance under balanced weights, yet pathway, statistical and network evidence remain dependent. Preserving pre-existing ranks avoids retrospective third-study score inflation, but not discovery winner's curse. Follow-up should prespecify candidates, use matched cohorts and include targeted expression/protein/functional assays; none were undertaken here. The associated publication's experimental results are not experiments performed by this project.

## Limitations

{limitations}

Additional limits include unresolved third deposited-versus-published sample counts, no new primary filter-refit grid, gene dependence in overlap tests, downstream exploratory multiplicity, and heuristic ranking ties. Forest intervals are within-study approximate Wald intervals, not heterogeneity-adjusted meta-analytic intervals. Human discrimination, causality, independent external second-environment reproduction and container execution remain unavailable.

## Conclusions

NeuroGene Atlas provides an auditable computational reanalysis with real study-specific effects, reproducible figures and transparent candidate evidence. Cross-model support motivates hypotheses, not clinical or causal claims. Its principal contribution is an evidence trail that makes selection and uncertainty visible.

## References

{references}

## Figure Legends

"""
    manifest=json.loads((PUB/"figure_manifest.json").read_text())
    manuscript+="\n\n".join(f"**Figure {i}. {f['title']}.** {f['caption']} Parameters: `{json.dumps(f['parameters'])}`. Files: `results/publication/{f['name']}.pdf`, `.svg`, `.csv`." for i,f in enumerate(manifest,1))
    manuscript+=f"\n\n## Supplementary Materials\n\nS1: original GEO review/metadata. S2: study-specific inference/shrinkage/session outputs. S3: all-gene effects and selection audit. S4: {len(sensitivity)} threshold/context/filter/outlier setting rows. S5: study-specific and common-background Reactome. S6: full STRING mapping/edges/metrics. S7: candidate evidence and preserved sensitivity ranks. S8: vector figures, source CSVs, captions/parameters/hashes. S9: actual software validation and clean-release manifests. Supplements are computational artifacts, not independent experiments.\n"
    (ROOT/"SCIENTIFIC_MANUSCRIPT_DRAFT.md").write_text(manuscript)
    vpath=ROOT/"results/validation/final_validation.json"
    validation=json.loads(vpath.read_text()) if vpath.exists() else {"status":"pending"}
    observed={"status":"pending Phase 4; historical Phase 3 record is not current validation"}
    if validation.get("phase")==4:observed=validation
    report=f"# NeuroGene Atlas Scientific Report\n\nPhase 4 study-aware reanalysis.\n\n## Summary\n\n{summary}\n\n## Datasets and Methods\n\n"+formal[formal.index("## Required Corrections"):]
    report+="\n\n## Exploratory Candidate Prioritization\n\nPreserved ranks; separate third-study evidence. Exploratory candidates, not validated biomarkers.\n\n## Observed Software Validation\n\n```json\n"+json.dumps(observed,indent=2)+"\n```\n\n## Publication Figures\n\n"
    body=markdown.markdown(report,extensions=["tables","fenced_code"])
    for i,f in enumerate(manifest,1):
        encoded=base64.b64encode((PUB/f"{f['name']}.png").read_bytes()).decode()
        body+=f'<figure><h3>Figure {i}. {html.escape(f["title"])}</h3><img src="data:image/png;base64,{encoded}" alt="{html.escape(f["title"])}"><figcaption>{html.escape(f["caption"])}</figcaption></figure>'
    style="body{font:14px Arial,sans-serif;max-width:1050px;margin:40px auto;padding:0 24px;color:#243335;line-height:1.6}h1{font-size:30px}h2{font-size:21px;border-bottom:1px solid #ccd9d6;margin-top:32px}table{border-collapse:collapse;width:100%;font-size:10px}td,th{padding:6px;border-bottom:1px solid #dce5e4;text-align:left;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:10px}img{max-width:100%;max-height:530px}figure{margin:24px 0}figcaption{font-size:12px;color:#536482}a{color:#148780}@media print{body{font-size:10px;margin:0;padding:0}h2,h3{break-after:avoid}figure,tr{break-inside:avoid}img{max-height:380px}pre{font-size:7px}table{font-size:8px}figcaption{font-size:9px}}"
    reports=ROOT/"results/reports"
    historical=reports/"phase3"
    historical.mkdir(exist_ok=True)
    for ext in ("html","pdf"):
        old=reports/f"NeuroGene_Atlas_Scientific_Report.{ext}"
        if old.exists() and not (historical/old.name).exists():shutil.copy2(old,historical/old.name)
    (reports/"NeuroGene_Atlas_Scientific_Report.html").write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>NeuroGene Atlas Scientific Report</title><style>'+style+'</style></head><body>'+body+'</body></html>')
    with zipfile.ZipFile(PUB/"NeuroGene_Atlas_Publication_Figures.zip","w",zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PUB.iterdir()):
            if path.suffix in (".pdf",".svg",".png",".csv",".json"):archive.write(path,path.name)
    print("Audit, manuscript, standalone HTML and vector collection generated from actual tables")


if __name__=="__main__":main()
