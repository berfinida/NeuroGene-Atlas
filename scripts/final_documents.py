"""Generate evidence-bound final audits; no analysis results or historical records overwritten."""
import base64
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import shutil

import markdown
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "results/validation/phase5"


def table(frame):
    rows = ["| " + " | ".join(frame.columns) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    for row in frame.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(f"{v:.6g}" if isinstance(v, float) else str(v).replace("|", "/") for v in row) + " |")
    return "\n".join(rows)


def main():
    repro = json.loads((VALIDATION / "reproduction.json").read_text())
    observed = json.loads((VALIDATION / "tests.json").read_text()) if (VALIDATION / "tests.json").exists() else {"status": "unverified", "checks": {}}
    audit = json.loads((ROOT / "results/phase4/audit.json").read_text())
    pair = pd.read_csv(ROOT / "results/phase4/pairwise_summary.csv")
    selected = pd.read_csv(ROOT / "results/phase4/selection_audit.csv")
    evidence = pd.read_csv(ROOT / "results/phase4/candidate_evidence.csv")
    methods = json.loads((ROOT / "results/discovery/candidates/methods.json").read_text())
    figure_manifest = json.loads((ROOT / "results/publication/figure_manifest.json").read_text())
    reproduction_table = table(pd.DataFrame([{"Study": study, "Tables matched": len(s["tables"]),
                                             "Maximum numeric difference": max(v["max_absolute_difference"] for v in s["tables"].values()),
                                             "Status": s["status"]} for study, s in repro["studies"].items()]))
    compare_table = table(pair[["study_a", "study_b", "universe", "overlap", "concordant", "discordant", "overlap_log10_p"]])
    bias_table = table(selected[selected.subset.isin(["all_common_finite_effects", "DEG_intersection"])][["study_a", "study_b", "subset", "genes", "sign_concordance", "pearson_r", "spearman_rho"]])
    stamp = datetime.now(timezone.utc).isoformat()
    run_commands = """```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python scripts/final_reproduction.py --rscript Rscript
.venv/bin/python scripts/final_validate.py --build-only --api-url http://127.0.0.1:8005
.venv/bin/python scripts/final_validate.py --base-url http://127.0.0.1:3005 --api-url http://127.0.0.1:8005
.venv/bin/python scripts/final_documents.py
NEUROGENE_REPORT_STEM=NeuroGene_Atlas_Scientific_Report_FINAL node frontend/scripts/report-pdf.mjs
.venv/bin/python scripts/final_release.py package
.venv/bin/python scripts/final_release.py verify
```"""
    actual = "Exact executable paths and command ledgers are retained in private local audit records, not in the public source. The commands below are portable equivalents, not a claim that the deleted `.venv` was used in this audit. Python used a fresh temporary environment; Node v22.23.1."
    scientific = f"""# Final Scientific Audit

Phase 5 / generated {stamp}. This is an audit of existing computational work, not new wet-lab or clinical validation.

## Executive Decision

Original count inputs and numerical outputs remain preserved. Three isolated per-study DESeq2 reruns reconstructed inputs and reproduced 24 stored CSV tables. The previously reported 976/973/3 intersection is numerically supported, but selected-DEG agreement is not an unbiased replication rate. The platform supports exploratory, heterogeneous mouse cross-model research. Scientific publication remains conditional on resolving metadata and independence ambiguities and appropriately limiting novelty and biomarker language.

## Input, Design and Identifier Audit

Original GEO matrices/counts: `data/raw/GSE156496/`, `data/raw/GSE132741/`, `data/raw/GSE284723/`. Prepared matrices and metadata: corresponding `data/processed/` directories. R scripts: `scripts/rna_seq/deseq2_gse156496.R`, `scripts/discovery/independent_deseq2.R`, `scripts/discovery/third_deseq2.R`. Each rerun was isolated in a temporary root; no stored result was replaced. SHA-256 verified unchanged for {repro.get('original_scientific_files_unchanged', 0)} original scientific files.

Discovery: six deposited bulk TA libraries, three WT/three D51; original GEO age one month. Constitutive exon-51 designation follows GEO; conflicting publication/model shorthand is not resolved by renaming the samples. External: 15 GEO-labelled 30-week TA libraries with 15 unique mouse IDs, seven WT/eight mdx. Excluded blood, other genotypes and younger TA; no repeated-mouse pseudo-replication in this selected metadata. Third: five floxed controls/four conditional mKO, 4-6 months. Floxed controls are not WT. GEO prose specifies ten, deposited counts nine, publication figure legend eight. Retain all nine deposited libraries without outcome-driven exclusion. Discovery/third individual-animal IDs and explicit sex fields are incomplete; library uniqueness cannot independently establish biological independence.

External 24,451 symbols map to 23,414 exact unique mm10 identifiers; 1,037 unresolved/ambiguous symbols remain excluded. Third 57,010 gene rows are integers, five HTSeq summary rows excluded; terminal Ensembl versions removed without rounding, aliases or duplicate collapse. Stable IDs do not reconcile counting definitions between mm10 and GRCm39/Gencode M32. GEO versus publication processing descriptions differ. No FASTQ realignment was performed. Audit tests reconstruct original matrices and sample ordering, not only filenames.

## Statistical Integrity and Reproduction

Raw nonnegative integer counts, study-specific `~condition` models and own control references; median-ratio normalization, parametric dispersions, Wald tests, independent filtering and BH at alpha 0.05. Primary threshold >=10 counts in >=3 samples. DEGs use padj<0.05 and |unshrunken log2FC|>1, a post hoc filter rather than a nonzero-null test. apeglm effects remain separate and original inference is preserved. Contrast reversal is checked in executed R scripts; BH is independently reconstructed in Python.

{reproduction_table}

All maximum numeric differences are computed from parsed CSV numeric columns; missingness, identifiers, sample ordering and nonnumeric fields are also compared. Tolerances: rtol=1e-8, atol=1e-10. R 4.4.3, DESeq2 1.46.0, apeglm 1.28.0; jsonlite 2.0.0 for scripts recording it. Full comparisons/commands: `results/validation/phase5/reproduction.json`, logs `reproduction_00.log` through `reproduction_04.log`. This is same-host, same-R-environment reproduction, not a second R installation, independent analyst, or independent biological experiment. Historical Phase 3 reproduction remains separately available.

Discovery: 14,359 fitted genes/1,499 DEGs; external 14,494/2,419; third 15,009/1,817. Original summary and package-version fields were compared during reruns. Discovery/third groups do not meet default seven-replicate replacement eligibility. External default replaces 1,243 genes; full no-replacement refit has 2,019 DEGs and 13,252 valid-FDR genes. The external no-replacement table was also reproduced exactly. Third filter fits give 1,490 and 1,669 DEGs, and diagnostic Cook-disabled results remain separate.

## QC and Context Confounding

PCA uses VST blind=False and the 500 highest-variance fitted genes, separately within each study. Six/15/nine libraries are retained. No PCA separation establishes causal effects or proves animal independence. Prepared-versus-fitted library sums are now separately displayed for external studies. Sample distances, normalization, count alignment and PCA tables are tested. Sources: `results/phase4/qc/` and study `deseq2/` directories.

Age, genotype, conditional deletion, reference controls, lab/workflow, bulk composition, fasting and incomplete batch/sex metadata differ. These factors cannot be separated by merging count matrices or fitting an unsupported pooled model. No pooling/meta-analysis was undertaken. The external fasting-duration model is diagnostic, not proof of deconfounding: continuous covariates disable DESeq2 automatic Cook filtering, changing valid-FDR coverage from 13,252 to 14,494; its 2,958 DEGs mix eligibility and estimate changes. The context fit was not independently rerun in Phase 5. Fixed-universe comparisons remain available. No claim of complete batch adjustment is warranted.

## Cross-Study Selection Audit

{compare_table}

{bias_table}

Discovery/mdx all-common-finite effects have 75.2868% sign agreement, compared with 99.6926% in the selected intersection. Pearson/Spearman all-gene effects are 0.765091/0.685188. Selected signs are strongly skewed; the descriptive marginal-sign expectation in the intersection is 86.2466%, not 50%. Strong shared effects, selection, winner's curse and biological composition plausibly contribute; this audit does not quantify a causal contribution for any factor. Hypergeometric log-survival avoids numeric underflow, but assumes exchangeability and does not account for correlated genes. Small overlap p-values do not establish generalizable biomarkers.

The entire all-effect subset, common-valid-FDR subset, study-A-selected subset and DEG intersection were independently recalculated in `tests/test_phase5.py`. Sources: `results/phase4/selection_audit.csv`, `pairwise_summary.csv`, `statistical_sensitivity.csv` (108 rows). No-replacement discovery/mdx intersection is 896, with 893 concordant and three discordant. Existing sensitivity does not include every conceivable combination, a new primary filter grid, or a no-replacement mdx/conditional grid; candidate stability separately requires external no-replacement evidence. Perturbations are not confidence intervals.

## Pathways, Networks and Candidates

Reactome v95, study-specific valid-FDR/annotation-mapped universes, term sizes 10-500 and complete BH families including zero overlaps. Default shared all-DEG enriched terms: 30 discovery/mdx, 34 discovery/conditional, 29 mdx/conditional. Separate common-background sensitivity is retained. Enrichment depends on cutoffs and annotation; BH within each family is not a correction for all exploratory analyses. Tests recompute eligible families, hypergeometric tails, overlaps and BH.

STRING v12.0/taxon 10090 cached raw responses support 1,408 unique gene/protein mappings and 17,872 non-self undirected associations >=0.4 (4,646 >=0.7). Every component score, raw mapping and full-graph metric at 0.4/0.7/0.9 is tested, including isolates. Degree, degree/(n-1), confidence-weighted PageRank/Louvain and 64-pivot approximate betweenness use documented seeds. Evidence scores are confidence, not interaction strength. Functional associations may be indirect/text-mined and are not causality; hub-biased visualization is explicitly limited to 200 nodes.

All 1,499 original candidate scores/ranks remain unchanged. Every component, fixed missing-evidence denominator, rank/tie ordering and sensitivity scenario is reconstructed. Network is capped at 10% of balanced score, but saturated dependent components can still make network affect fine ranks. Eight scenarios are robustness perturbations, not biological validation. 572 candidates pass three default fits, external no replacement and both third count filters; 555 additionally pass diagnostic fasting adjustment. These are conditional exploratory candidates, not clinical biomarkers. Full evidence: `results/phase4/candidate_evidence.csv`; equations: `results/discovery/candidates/methods.json`.

## Evidence and Commands

{actual}

{run_commands}

## Unverified or Intentionally Omitted

No independent second R environment/analyst, FASTQ realignment, animal-ID confirmation for discovery/third, causal perturbation, human cohort, biomarker discrimination/calibration or clinical outcome evaluation. Docker lookup returned exit 1; no executable, container execution unverified. Full accessibility certification and real-device/cross-browser coverage are not claimed. The source contains a Docker recipe, not a tested container release. Future publication should resolve sample provenance with depositors and prespecify a matched replication/functional validation plan.
"""
    cohort_table = table(pd.DataFrame(audit["cohorts"])[["accession", "groups", "age", "case", "reference", "genome"]])
    comparison = f"""# Dataset Comparison Summary

Generated {stamp}. Sources: `results/phase4/pairwise_summary.csv`, `selection_audit.csv`, `pathway_comparison.csv`, `statistical_sensitivity.csv`, original GEO metadata `results/phase4/original_sample_metadata.json`.

## Cohorts

{cohort_table}

Three separate mouse bulk tibialis anterior cohorts; no pooled model. The third comparison is conditional mKO versus floxed controls, not mdx/D51 versus WT. Sex fields and individual-animal IDs are incomplete for two cohorts. Third design/deposit/legend counts (10/9/8) remain unresolved; use all deposited libraries, not a retrospectively selected subset.

## Default Comparisons

{compare_table}

Universes require common nonmissing BH padj; finite-effect universes are larger (12,815 / 13,664 / 12,980). Thresholds padj<0.05, |unshrunken log2FC|>1. Log10 hypergeometric tails are descriptive and assume exchangeable genes. All-common correlations and selected agreement are distinct quantities.

{bias_table}

No-replacement discovery/mdx: 11,963 shared valid-FDR genes; 896 overlapping DEGs, 893 concordant/3 discordant. Third alternatives: 13,423 fitted genes/1,490 DEGs (count20) and 14,493/1,669 (minimum4), compared with default 15,009/1,817. Fasting adjustment changes Cook eligibility, so its 2,958 DEGs are not solely an estimate of fasting confounding. 108 existing perturbation rows are exported; not every joint setting is included. The shared pathway counts 30/34/29 refer to separate backgrounds and all-DEG families, not three-way intersection counts.

## Reproduction and Uncertainty

{reproduction_table}

Original 204 scientific files remained unchanged. Three default fits, external no-replacement and third filter/diagnostic fits were rerun in an isolated temporary root. The R environment is the same pinned installation; Python dependencies were freshly installed. Batch, age, genotype, sex, annotation and bulk composition limit interchangeability. No meta-analysis, clinical validation or causal inference. Exact commands/tolerances/versions: `results/validation/phase5/reproduction.json`; selection recalculation: `tests/test_phase5.py`. Reproducible invocation: `python scripts/final_reproduction.py --rscript Rscript`.
"""
    top_columns = ["gene_symbol", "gene_id", "rank_balanced", "score_balanced", "GSE156496_log2FoldChange", "GSE132741_log2FoldChange", "GSE284723_log2FoldChange", "sensitivity_rank_min", "sensitivity_rank_max", "three_study_filter_outlier_stable"]
    candidates = f"""# Candidate Gene Evidence

Generated {stamp}. Exploratory gene hypotheses, not validated diagnostic or therapeutic biomarkers.

## Explainable Evidence

Population: all 1,499 discovery DEGs. Original ranks were frozen before third-study evidence; third effects were not used to increase scores. Full per-study unshrunken/apeglm effects, SE, FDR, directions, missingness, pathway IDs, STRING metrics and alternative-fit flags: `results/phase4/candidate_evidence.csv`. Interactive comparison permits four candidates; forest intervals are approximate within-study log2FC +/-1.96 SE, not pooled estimates or selection-corrected intervals.

{table(evidence.nsmallest(10, 'rank_balanced')[top_columns])}

## Equations and Missingness

`S = sum(w_j * c_j * available_j) / sum(w_j)`. Each component is bounded [0,1]; missing is NA, contributes no confirmed support and never removes its preset denominator weight. Missing is not negative biological evidence. Deterministic ties use ascending gene ID and do not indicate biological preference.

{table(pd.DataFrame([{'Component': key, 'Balanced weight': methods['weights']['balanced'][key], 'Definition': value} for key, value in methods['components'].items()]))}

Statistical caps may saturate; pathway/STRING/statistical support is dependent and affected by discovery selection and literature bias. A 10% network cap does not prove rank insensitivity to degree. The nine sample pairs are not nine independent biological replicates; consistency is descriptive. Leave-pair-out effects use normalized means and pseudocount one, not refitted DESeq2 significance.

## Robustness

{table(pd.DataFrame(methods['sensitivity']))}

572 genes are concordant DEGs in three default fits plus external no replacement and two third count filters. 555 also retain diagnostic measured-fasting support; automatic Cook filtering differs in that fit. Neither count means stable at every FDR/effect cutoff. No-network top-50 overlap 39/50; no-pathway 38/50. Examples Itgax, Tyrobp, Itgb2, Cd68 and Trem2 are selected by original heuristic ranking, not independently validated discoveries. Bulk cell composition may contribute; no claim of cell-intrinsic pathogenicity follows.

## Verification and Limits

Executed component/rank/stability checks: `tests/test_phase4.py`, `tests/test_phase5.py`, current log `results/validation/phase5/python.log`. Use `python -m unittest discover -s tests -v`. Same-host full R reruns reproduce the input statistics, not the clinical utility of a score. Scores are not probabilities and no training/held-out accuracy, wet-lab perturbation or human outcome model was performed. Weight sensitivity is descriptive, not a confidence interval. Follow-up requires prespecified candidates, matched independent cohorts and functional evidence.
"""
    publication = f"""# Publication Readiness

Generated {stamp}. Assessment: **computational draft suitable for scientific coauthor review; not unconditional submission-ready or experimentally validated**.

## Completed Research

Separate DESeq2/apeglm analysis of three deposited mouse TA cohorts, independent same-host raw-count reconstruction/rerun, selection-bias audit, tested-universe DEG overlap, study-specific/common-background enrichment, verified STRING association analysis and explainable candidate evidence. Fourteen vector PDF/SVG figure sets have complete captions, parameters, source CSVs, PNG previews and SHA-256 in `results/publication/figure_manifest.json`. No raster layers in SVGs; source hashes, archive membership and report numerical facts are tested.

`SCIENTIFIC_MANUSCRIPT_DRAFT.md` has a structured abstract, introduction, methods, results, discussion, limitations, conclusions, verifiable references, figure legends and supplements. Its research question is cross-model transcriptomic consistency and robustness, not clinical diagnosis. Bulk counts are distinguished from the discovery publication's single-nucleus experiments; external patient/blood findings are not findings of this muscle-only project.

## Statistical Interpretation

976 overlapping DEGs/973 concordant are supported, but 75.3% all-common-gene agreement versus 99.7% selected intersection agreement must both be reported. Pearson/Spearman universes must be stated, not mixed. Hypergeometric p-values are descriptive under gene dependence. BH applies per declared family, not across every exploratory choice. Positive effects use each study's own case/control, including floxed controls. Shrinkage and original inference remain separate. Fasting adjustment also changes Cook eligibility; no causal deconfounding claim is defensible.

## Novelty and References

Novelty is an inspectable, study-aware reanalysis and evidence platform, not first identification of dystrophin-response pathways. The third original publication already compares earlier dystrophin cohorts. No exhaustive novelty search, priority claim or authorship/affiliation fabrication is made. Reference identifiers/title matching checked against primary records and official methods where accessible:

- [Chemello et al., PNAS 2020, PMID 33148801](https://pubmed.ncbi.nlm.nih.gov/33148801/), DOI 10.1073/pnas.2018391117; bulk subset here.
- [Peripheral blood transcriptome profiling..., PMID 33751844](https://pubmed.ncbi.nlm.nih.gov/33751844/); only deposited mouse TA used here.
- [Karuppasamy et al., Communications Biology 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12673120/), DOI 10.1038/s42003-025-09128-y; publication/deposit discrepancy remains.
- [Love, Huber and Anders, Genome Biology 2014](https://doi.org/10.1186/s13059-014-0550-8); negative-binomial inference, not exploratory Python t statistics.
- [Zhu, Ibrahim and Love, Bioinformatics 2019, PMID 30395178](https://pubmed.ncbi.nlm.nih.gov/30395178/), DOI 10.1093/bioinformatics/bty895; title/identifier matched in the primary PubMed search record after direct DOI resolving failed.
- [STRING association scores](https://string-db.org/help/scores/), [STRING 2023, PMID 36370105](https://pubmed.ncbi.nlm.nih.gov/36370105/); confidence is not causality or interaction strength.
- [Reactome release 95 source mapping](https://download.reactome.org/95/Ensembl2Reactome.txt), bundled pinned mouse mapping with SHA-256.
- [Official DESeq2 vignette](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html); installed 1.46.0 vignette is the relevant historical runtime evidence.

Some direct NCBI opens returned a browser challenge/empty content; cached original GEO matrices and matching primary-search records were retained. Online title lookup is not independent sample-ID confirmation. Journal-style bibliography, author contributions, funding/conflicts, ethics/data-use statement and target-journal requirements must be completed by actual authors.

## Required Before Stronger Claims

Resolve third 10/9/8 sample counts and discovery exon nomenclature with depositors; confirm discovery/third animal independence and sex; assess batch/time and bulk composition with appropriate metadata rather than unsupported pooling. Obtain independent analyst/environment reproduction and prespecified matched biological validation. A clinical biomarker paper would additionally require human cohorts, discrimination/calibration, clinical confounder control and external prospective validation; none is present.

Figures are reusable source artifacts, not a guarantee of journal acceptance. Software test success establishes functionality/integrity, not experimental truth. Current new audit/report sources: `FINAL_SCIENTIFIC_AUDIT.md`, `DATASET_COMPARISON_SUMMARY.md`, `CANDIDATE_GENE_EVIDENCE.md`, `results/reports/NeuroGene_Atlas_Scientific_Report_FINAL.html`. Commands: `python scripts/final_documents.py`, `NEUROGENE_REPORT_STEM=NeuroGene_Atlas_Scientific_Report_FINAL node frontend/scripts/report-pdf.mjs`.
"""
    inventory = [
        ("Research overview / Dataset", "frontend/app/page.tsx", "Summary, original GEO registry, real PCA; three-study Dataset/QC selector", "DE/gene expression/pathway tools remain discovery-specific"),
        ("Quality control", "frontend/app/StudyInspector.tsx", "Per-study PCA, prepared/fitted totals, size factors, external Cook summaries, distance exports", "Primary additionally has heatmap/distance figures; no raw-read QC"),
        ("Differential expression", "backend/main.py /api/genes", "FDR/LFC/direction/estimate/search/sort/pagination/CSV", "Volcano/MA are static unshrunken figures, not an interactive estimate-switching chart"),
        ("Gene expression", "frontend/app/page.tsx", "Interactive per-sample raw/normalized/VST bars and gene search", "Discovery only; no cross-study normalized-count comparison"),
        ("Cross-Dataset Validation", "frontend/app/DiscoveryViews.tsx", "Two-study filtering/outliers/discordance/pagination/pathways", "Three-study evidence is in Study Evidence/Sensitivity, not a pooled comparison"),
        ("Functional enrichment", "backend/main.py /api/pathways", "Reactome search/FDR/direction/IDs/gene links/CSV", "No ranked GSEA or other ontology implementation"),
        ("STRING Network Explorer", "frontend/app/NetworkView.tsx", "Actual Cytoscape canvas, search, confidence, node/edge inspectors, communities, full exports", "DEG-induced graph; display<=200; indirect associations, no causality"),
        ("Candidate prioritization", "scripts/discovery/prioritize_candidates.py", "Six bounded components, five presets, eight rank scenarios, fixed missing denominator", "Heuristic, frozen original rank; third evidence not retrospectively added"),
        ("Study Evidence", "frontend/app/ResearchViews.tsx", "Search/stability/pagination, four-gene per-study effects/FDR/SE comparison", "Within-study Wald intervals, not pooled/selection-adjusted"),
        ("Statistical sensitivity", "results/phase4/statistical_sensitivity.csv", "108 real perturbation rows, pair/FDR controls, plots/exports", "Not exhaustive combinations or confidence intervals"),
        ("Publication / provenance", "results/publication/figure_manifest.json", "14 vector/source sets, captions/parameters/SHA, fit/reproduction indicators", "Historical Phase 4 and new Phase 5 statuses distinguished"),
        ("Scientific Reports / exports", "backend/main.py", "Primary ZIP, HTML/PDF, source tables, vectors, final audit files", "No editable report builder or scheduled analysis service"),
    ]
    inventory_table = table(pd.DataFrame(inventory, columns=["Module", "Evidence path", "Implemented", "Limits / not implemented"]))
    test_rows = [{"Check": name, "Status": c["status"], "Exit": c.get("exit_code", "NA"), "Evidence": c.get("log", "NA")} for name, c in observed.get("checks", {}).items()]
    test_table = table(pd.DataFrame(test_rows)) if test_rows else "No Phase 5 tests observed yet."
    technical = f"""# Final Technical Audit

Generated {stamp}. Source inspected before edits; existing Next.js/FastAPI/Cytoscape architecture and all scientific outputs preserved. Current observed validation status: **{observed['status']}**. `results/validation/phase5/tests.json` is authoritative; Phase 3/4 records remain historical, not relabelled as new passes.

## Implemented Versus Documented Inventory

{inventory_table}

No database, authentication, public deployment hardening, task queue, automated FASTQ workflow, human cohort, trained biomarker model or complete accessibility certification is implemented. R environment recipe exists but container execution is unverified; Docker lookup exit 1. Manuscript/figures are research artifacts, not peer-reviewed validation.

## Defects and Repairs

- Dataset and QC views originally exposed only discovery despite three stored cohorts. Added strict three-study API selector and file-backed explorer; primary behavior preserved. Prepared and fitted library totals are separately labelled, avoiding a preprocessing-depth ambiguity.
- Fifth sensitivity scenario had no configured bar color; all five now have explicit colors.
- Missing allowed figure could cause a FileResponse runtime exception; explicit existence guard now returns HTTP 404 and a regression test covers it.
- Gene-search accepted a missing/empty query despite declared length constraint; now required and empty/missing return HTTP 422.
- Added a keyboard skip link and visible focus indicators. Basic label/keyboard/viewport tests pass where recorded; not full WCAG certification.
- Initial Phase 5 API audit runner could not import backend when executed as a script. Added root to import path. Error-state browser test matched both application alert and Next route announcer; scoped to the application error. Initial failed outcomes remain in `results/validation/phase5/history/`, not erased.

## Actual Checks

{test_table}

Scientific tests reconstruct integer inputs, sample alignment, BH, separate shrinkage, full selection universes/correlations, overlap tails, Reactome background/families, STRING scores/mappings/metrics, score components, tie order and stability. Live HTTP requests cover every registered API route template and download choice, independently of in-process TestClient tests. Playwright covers all twelve views, desktop/mobile, network canvas pixels, interaction/search/filter/pagination/downloads, switching, loading/error/retry, keyboard names, console errors and viewport overflow. A deliberate test-only simulated 503 is explicitly scoped; real scientific responses are never mocked for result assertions.

## Release, Cleanup and Operating Constraints

Source includes dependency manifests/locks, not installed `node_modules`/`.venv`. Research includes originals, real tables/figures, reports/manuscript, provenance and validation evidence. `.git`, `.next`, caches/temp/secrets and all old `release/` archives are excluded. Existing report ZIP and publication-figure ZIP are deliberately retained because download endpoints require them; these are not duplicated final releases. Old Phase 3/4 scientific artifacts remain on disk and labelled historical.

Final CRC/SHA checks and clean paired extraction are performed by `scripts/final_release.py`. Full clean verification installs dependencies afresh, starts actual extracted API/frontend and reruns Python/typecheck/build/browser tests. Until its machine record exists, extraction is unverified; details are separate from application passes to avoid circularly claiming archive tests from source-tree tests. R reproduction does not run again during extraction.

{actual}

{run_commands}

## Remaining Risk

Chromium emulation only, no Safari/Firefox/assistive-technology certification. Recharts 2.15.4 is deprecated upstream; npm audit has no known reported runtime vulnerabilities when current record passes, not proof of absence. Framework pinned versions are preserved to avoid an unrelated migration. API is local, read-only and lacks auth/rate limiting; public deployment needs a separate security review. Release checks cover bundled data, not future internet availability or all OS/Python combinations.
"""
    tests = f"""# Final Test Results

Generated {stamp}; overall source-tree Phase 5 status: **{observed['status']}**. Exact outcome/time/command records: `results/validation/phase5/tests.json`, `commands.json`, `live_api.json`, `playwright_results.json`. Historical counts are not current outcomes.

{test_table}

Python test count: {observed.get('checks',{}).get('python',{}).get('tests_run','unverified')}; API integration subset: {observed.get('checks',{}).get('python',{}).get('api_tests','unverified')}. Browser stats: `{json.dumps(observed.get('checks',{}).get('playwright',{}).get('stats',{}))}`. Source-tree production build, TypeScript, pip dependency check and runtime npm audit are distinct executed checks. Live HTTP coverage: {observed.get('checks',{}).get('live_api',{}).get('requests','unverified')} requests / {observed.get('checks',{}).get('live_api',{}).get('api_route_templates','unverified')} registered API route templates.

Three-study R rerun status: **{repro['status']}**, 24 matching CSV tables, maximum numerical difference zero, rtol 1e-8/atol 1e-10. Versions and six prepared input tables also verified. Original 204 scientific file hashes unchanged. Original calls, current temporary paths and per-stage logs in `reproduction.json`. Same R environment/host, not second-environment replication. Context fit and FASTQ alignment were not newly rerun.

## Observed Failures and Retests

First complete Phase 5 run: Python 58 passed; browser 28 passed/2 failed because the test alert locator also matched Next's route announcer. Live API runner failed on missing root import path. Both tools repaired, then rerun. Later records replace the current summary while history retains exact failures; no scientific table modified to satisfy a test. Any subsequent failures are retained similarly.

## Archive and Clean Extraction

Do not infer clean-extraction passes from these source tests. Final machine outcomes are `release/final_release_validation.json` and `release/final_extracted_validation.json`; external SHA file is `release/RELEASE_MANIFEST_SHA256.txt`. The extracted test logs and exact dependency/build/server/test commands are retained under `release/final_extracted_logs/`. When these do not exist yet, release verification is pending. The FINAL archives contain the source-test records and critical data; post-sealing extraction evidence is provided separately so the checked ZIP bytes do not change after verification.

Docker: executable lookup exit 1; not tested. Browser coverage Chromium desktop/mobile emulation, no flaky/skipped tests claimed unless current machine stats support that. Accessibility coverage is basic keyboard/names/focus/overflow checks, not complete conformance.

{actual}

{run_commands}
"""
    documents = {"FINAL_SCIENTIFIC_AUDIT.md": scientific, "FINAL_TECHNICAL_AUDIT.md": technical,
                 "PUBLICATION_READINESS.md": publication, "DATASET_COMPARISON_SUMMARY.md": comparison,
                 "CANDIDATE_GENE_EVIDENCE.md": candidates, "FINAL_TEST_RESULTS.md": tests}
    copies = ROOT / "results/final/audit"
    copies.mkdir(parents=True, exist_ok=True)
    for name, content in documents.items():
        (ROOT / name).write_text(content)
        (copies / name).write_text(content)
    for name in ("SCIENTIFIC_MANUSCRIPT_DRAFT.md", "SCIENTIFIC_AUDIT_REPORT.md"):
        shutil.copy2(ROOT / name, copies / name)
    files = [p for base in ("frontend/app", "backend", "scripts", "tests", "docs", "config", "data", "results")
             for p in (ROOT / base).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    inventory_record = {"generated_utc": stamp, "files": [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size} for p in sorted(files)],
                        "modules": [dict(zip(["module", "source", "implemented", "limits"], row)) for row in inventory],
                        "preserved_historical": ["results/validation/phase3", "results/validation/phase4_failures", "results/reports/phase3", "release/phase3"],
                        "obsolete_not_deleted": ["scripts/discovery/scientific_report.py (Phase 3 generator; use final_documents.py for FINAL report)"]}
    (VALIDATION / "inventory.json").write_text(json.dumps(inventory_record, indent=2) + "\n")
    body = markdown.markdown("\n\n".join(documents.values()), extensions=["tables", "fenced_code"])
    for figure in figure_manifest:
        encoded = base64.b64encode((ROOT / "results/publication" / f"{figure['name']}.png").read_bytes()).decode()
        body += f'<figure><h2>{html.escape(figure["title"])}</h2><img src="data:image/png;base64,{encoded}" alt="{html.escape(figure["title"])}"><figcaption>{html.escape(figure["caption"])}</figcaption></figure>'
    css = "body{font:14px Arial,sans-serif;max-width:1050px;margin:35px auto;padding:20px;color:#243335;line-height:1.5}h1{font-size:28px}h2{font-size:20px}table{border-collapse:collapse;width:100%;font-size:10px}th,td{border-bottom:1px solid #ccd9d6;padding:5px;text-align:left;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:10px}img{max-width:100%;max-height:520px}figure{margin:24px 0}figcaption{font-size:12px}a{color:#12665f}@media print{body{font-size:10px;margin:0;padding:0}table{font-size:7px}pre{font-size:7px}figure,tr{break-inside:avoid}h1,h2{break-after:avoid}img{max-height:380px}figcaption{font-size:9px}}"
    report = ROOT / "results/reports/NeuroGene_Atlas_Scientific_Report_FINAL.html"
    report.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>NeuroGene Atlas Final Scientific Audit</title><style>' + css + '</style></head><body>' + body + '</body></html>')
    print(json.dumps({"documents": list(documents), "report": str(report.relative_to(ROOT)), "observed_validation_status": observed['status'], "inventory_files": len(files)}, indent=2))


if __name__ == "__main__":
    main()
