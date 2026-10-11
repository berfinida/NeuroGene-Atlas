# Final Scientific Audit

Phase 5 / generated 2026-10-11T18:09:01.302750+00:00. This is an audit of existing computational work, not new wet-lab or clinical validation.

## Executive Decision

Original count inputs and numerical outputs remain preserved. Three isolated per-study DESeq2 reruns reconstructed inputs and reproduced 24 stored CSV tables. The previously reported 976/973/3 intersection is numerically supported, but selected-DEG agreement is not an unbiased replication rate. The platform supports exploratory, heterogeneous mouse cross-model research. Scientific publication remains conditional on resolving metadata and independence ambiguities and appropriately limiting novelty and biomarker language.

## Input, Design and Identifier Audit

Original GEO matrices/counts: `data/raw/GSE156496/`, `data/raw/GSE132741/`, `data/raw/GSE284723/`. Prepared matrices and metadata: corresponding `data/processed/` directories. R scripts: `scripts/rna_seq/deseq2_gse156496.R`, `scripts/discovery/independent_deseq2.R`, `scripts/discovery/third_deseq2.R`. Each rerun was isolated in a temporary root; no stored result was replaced. SHA-256 verified unchanged for 204 original scientific files.

Discovery: six deposited bulk TA libraries, three WT/three D51; original GEO age one month. Constitutive exon-51 designation follows GEO; conflicting publication/model shorthand is not resolved by renaming the samples. External: 15 GEO-labelled 30-week TA libraries with 15 unique mouse IDs, seven WT/eight mdx. Excluded blood, other genotypes and younger TA; no repeated-mouse pseudo-replication in this selected metadata. Third: five floxed controls/four conditional mKO, 4-6 months. Floxed controls are not WT. GEO prose specifies ten, deposited counts nine, publication figure legend eight. Retain all nine deposited libraries without outcome-driven exclusion. Discovery/third individual-animal IDs and explicit sex fields are incomplete; library uniqueness cannot independently establish biological independence.

External 24,451 symbols map to 23,414 exact unique mm10 identifiers; 1,037 unresolved/ambiguous symbols remain excluded. Third 57,010 gene rows are integers, five HTSeq summary rows excluded; terminal Ensembl versions removed without rounding, aliases or duplicate collapse. Stable IDs do not reconcile counting definitions between mm10 and GRCm39/Gencode M32. GEO versus publication processing descriptions differ. No FASTQ realignment was performed. Audit tests reconstruct original matrices and sample ordering, not only filenames.

## Statistical Integrity and Reproduction

Raw nonnegative integer counts, study-specific `~condition` models and own control references; median-ratio normalization, parametric dispersions, Wald tests, independent filtering and BH at alpha 0.05. Primary threshold >=10 counts in >=3 samples. DEGs use padj<0.05 and |unshrunken log2FC|>1, a post hoc filter rather than a nonzero-null test. apeglm effects remain separate and original inference is preserved. Contrast reversal is checked in executed R scripts; BH is independently reconstructed in Python.

| Study | Tables matched | Maximum numeric difference | Status |
| --- | --- | --- | --- |
| GSE156496 | 8 | 0 | passed |
| GSE132741 | 6 | 0 | passed |
| GSE284723 | 10 | 0 | passed |

All maximum numeric differences are computed from parsed CSV numeric columns; missingness, identifiers, sample ordering and nonnumeric fields are also compared. Tolerances: rtol=1e-8, atol=1e-10. R 4.4.3, DESeq2 1.46.0, apeglm 1.28.0; jsonlite 2.0.0 for scripts recording it. Full comparisons/commands: `results/validation/phase5/reproduction.json`, logs `reproduction_00.log` through `reproduction_04.log`. This is same-host, same-R-environment reproduction, not a second R installation, independent analyst, or independent biological experiment. Historical Phase 3 reproduction remains separately available.

Discovery: 14,359 fitted genes/1,499 DEGs; external 14,494/2,419; third 15,009/1,817. Original summary and package-version fields were compared during reruns. Discovery/third groups do not meet default seven-replicate replacement eligibility. External default replaces 1,243 genes; full no-replacement refit has 2,019 DEGs and 13,252 valid-FDR genes. The external no-replacement table was also reproduced exactly. Third filter fits give 1,490 and 1,669 DEGs, and diagnostic Cook-disabled results remain separate.

## QC and Context Confounding

PCA uses VST blind=False and the 500 highest-variance fitted genes, separately within each study. Six/15/nine libraries are retained. No PCA separation establishes causal effects or proves animal independence. Prepared-versus-fitted library sums are now separately displayed for external studies. Sample distances, normalization, count alignment and PCA tables are tested. Sources: `results/phase4/qc/` and study `deseq2/` directories.

Age, genotype, conditional deletion, reference controls, lab/workflow, bulk composition, fasting and incomplete batch/sex metadata differ. These factors cannot be separated by merging count matrices or fitting an unsupported pooled model. No pooling/meta-analysis was undertaken. The external fasting-duration model is diagnostic, not proof of deconfounding: continuous covariates disable DESeq2 automatic Cook filtering, changing valid-FDR coverage from 13,252 to 14,494; its 2,958 DEGs mix eligibility and estimate changes. The context fit was not independently rerun in Phase 5. Fixed-universe comparisons remain available. No claim of complete batch adjustment is warranted.

## Cross-Study Selection Audit

| study_a | study_b | universe | overlap | concordant | discordant | overlap_log10_p |
| --- | --- | --- | --- | --- | --- | --- |
| GSE156496 | GSE132741 | 12814 | 976 | 973 | 3 | -592.485 |
| GSE156496 | GSE284723 | 13659 | 870 | 868 | 2 | -570.219 |
| GSE132741 | GSE284723 | 12976 | 909 | 895 | 14 | -485.931 |

| study_a | study_b | subset | genes | sign_concordance | pearson_r | spearman_rho |
| --- | --- | --- | --- | --- | --- | --- |
| GSE156496 | GSE132741 | all_common_finite_effects | 12815 | 0.752868 | 0.765091 | 0.685188 |
| GSE156496 | GSE132741 | DEG_intersection | 976 | 0.996926 | 0.843744 | 0.722734 |
| GSE156496 | GSE284723 | all_common_finite_effects | 13664 | 0.706821 | 0.761198 | 0.618918 |
| GSE156496 | GSE284723 | DEG_intersection | 870 | 0.997701 | 0.873269 | 0.758705 |
| GSE132741 | GSE284723 | all_common_finite_effects | 12980 | 0.660092 | 0.658851 | 0.511896 |
| GSE132741 | GSE284723 | DEG_intersection | 909 | 0.984598 | 0.824754 | 0.695303 |

Discovery/mdx all-common-finite effects have 75.2868% sign agreement, compared with 99.6926% in the selected intersection. Pearson/Spearman all-gene effects are 0.765091/0.685188. Selected signs are strongly skewed; the descriptive marginal-sign expectation in the intersection is 86.2466%, not 50%. Strong shared effects, selection, winner's curse and biological composition plausibly contribute; this audit does not quantify a causal contribution for any factor. Hypergeometric log-survival avoids numeric underflow, but assumes exchangeability and does not account for correlated genes. Small overlap p-values do not establish generalizable biomarkers.

The entire all-effect subset, common-valid-FDR subset, study-A-selected subset and DEG intersection were independently recalculated in `tests/test_phase5.py`. Sources: `results/phase4/selection_audit.csv`, `pairwise_summary.csv`, `statistical_sensitivity.csv` (108 rows). No-replacement discovery/mdx intersection is 896, with 893 concordant and three discordant. Existing sensitivity does not include every conceivable combination, a new primary filter grid, or a no-replacement mdx/conditional grid; candidate stability separately requires external no-replacement evidence. Perturbations are not confidence intervals.

## Pathways, Networks and Candidates

Reactome v95, study-specific valid-FDR/annotation-mapped universes, term sizes 10-500 and complete BH families including zero overlaps. Default shared all-DEG enriched terms: 30 discovery/mdx, 34 discovery/conditional, 29 mdx/conditional. Separate common-background sensitivity is retained. Enrichment depends on cutoffs and annotation; BH within each family is not a correction for all exploratory analyses. Tests recompute eligible families, hypergeometric tails, overlaps and BH.

STRING v12.0/taxon 10090 cached raw responses support 1,408 unique gene/protein mappings and 17,872 non-self undirected associations >=0.4 (4,646 >=0.7). Every component score, raw mapping and full-graph metric at 0.4/0.7/0.9 is tested, including isolates. Degree, degree/(n-1), confidence-weighted PageRank/Louvain and 64-pivot approximate betweenness use documented seeds. Evidence scores are confidence, not interaction strength. Functional associations may be indirect/text-mined and are not causality; hub-biased visualization is explicitly limited to 200 nodes.

All 1,499 original candidate scores/ranks remain unchanged. Every component, fixed missing-evidence denominator, rank/tie ordering and sensitivity scenario is reconstructed. Network is capped at 10% of balanced score, but saturated dependent components can still make network affect fine ranks. Eight scenarios are robustness perturbations, not biological validation. 572 candidates pass three default fits, external no replacement and both third count filters; 555 additionally pass diagnostic fasting adjustment. These are conditional exploratory candidates, not clinical biomarkers. Full evidence: `results/phase4/candidate_evidence.csv`; equations: `results/discovery/candidates/methods.json`.

## Evidence and Commands

Exact executable paths and command ledgers are retained in private local audit records, not in the public source. The commands below are portable equivalents, not a claim that the deleted `.venv` was used in this audit. Python used a fresh temporary environment; Node v22.23.1.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python scripts/final_reproduction.py --rscript Rscript
.venv/bin/python scripts/final_validate.py --build-only --api-url http://127.0.0.1:8005
.venv/bin/python scripts/final_validate.py --base-url http://127.0.0.1:3005 --api-url http://127.0.0.1:8005
.venv/bin/python scripts/final_documents.py
NEUROGENE_REPORT_STEM=NeuroGene_Atlas_Scientific_Report_FINAL node frontend/scripts/report-pdf.mjs
.venv/bin/python scripts/final_release.py package
.venv/bin/python scripts/final_release.py verify
```

## Unverified or Intentionally Omitted

No independent second R environment/analyst, FASTQ realignment, animal-ID confirmation for discovery/third, causal perturbation, human cohort, biomarker discrimination/calibration or clinical outcome evaluation. Docker lookup returned exit 1; no executable, container execution unverified. Full accessibility certification and real-device/cross-browser coverage are not claimed. The source contains a Docker recipe, not a tested container release. Future publication should resolve sample provenance with depositors and prespecify a matched replication/functional validation plan.
