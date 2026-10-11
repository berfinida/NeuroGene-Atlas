# Scientific Audit Report

## Scope and Evidence

Phase 4 audit of supplied count matrices, original GEO sample fields, DESeq2 objects, cross-model comparisons, Reactome v95, cached STRING v12.0 and exploratory rankings. Evidence is under `results/phase4/` and `data/raw/`. No FASTQ realignment, new wet-lab experiments or patient outcomes were analyzed.

## Required Corrections

1. **Corrected:** Original GSE156496 sample fields report one-month age, not unavailable. Current methods/limitations/API interpretation corrected; historical Phase 3 artifacts and numerical results retained.
2. **Unresolved:** Third-study GEO design says five mice/group, but nine libraries are deposited (five controls/four mKO). The publication figure legend describes four/group. All nine deposited libraries were used; no control was removed without a verified exclusion reason. These outputs need not match published DEG counts.
3. **Unresolved:** Third-study design prose says expected counts/FPKM, but processing specifies HTSeq-count and workbook values are integers. GSE132741 GEO processing mentions Cufflinks while supplied files are integer HTSeq-format counts. No counts were rounded or replaced by FPKM.
4. **Unknown:** Sex is not explicit in these GEO sample fields. The third /Y genotype suggests male, but is not a sample sex annotation. Individual animal IDs are explicit for fifteen selected external animals, not discovery/third libraries. Library uniqueness is not independent verification of animal uniqueness.
5. **Nomenclature caution:** Third-study article describes its previous CRISPR comparison as exon 52, whereas discovery GEO labels specify exon 51. Retain deposited contrasts; do not silently reassign genotype to agree with the article.

## Sample Metadata and Study Design

| accession | age | groups | case | reference | genome |
| --- | --- | --- | --- | --- | --- |
| GSE156496 | 1 month | 3 WT / 3 D51 | D51 (exon 51 deletion) | WT | mm10 |
| GSE132741 | 30 weeks | 7 WT / 8 mdx | mdx | WT | mm10 symbol bridge |
| GSE284723 | 4-6 months | 5 controls / 4 mKO | Dmd flox52/Y: HSA mKO | Dmd flox52/Y (not WT) | GRCm39 Gencode M32 |

Original fields, including genotype and fasting times, are exported in `original_sample_metadata.json`. External fasting intervals are 274-435 min (WT; mean 339.43) and 275-390 min (mdx; mean 321.875). Fifteen unique animal IDs are verified. Exploratory context model: `~fasting_hours_centered+condition`, count replacement disabled. Clock times interpreted as same-day collection; fasting may be a mediator or proxy, not necessarily an appropriate causal covariate. No outcome-driven sample exclusions or cross-study count pooling.

## Identifier and Input Integrity

Primary input hashes and sample ordering are verified. External exact case-sensitive, unique symbol-to-Ensembl bridge retains 23,414/24,451 symbols (1,037 unresolved/ambiguous excluded), without alias guessing. Third workbook contains 57,010 gene rows plus five HTSeq summary rows. Summary rows are excluded and separately exported. Only Ensembl version suffixes are removed; duplicate stable IDs prohibited. All nine gene-count columns are nonnegative integers, aligned by GEO title/accession/genotype. Stable IDs do not remove GRCm39/M32 versus mm10 counting-definition differences. Input/output SHA-256 files are bundled.

## DESeq2 and QC Verification

- GSE156496: 14,359 fitted genes, 6 libraries; integer fitted counts, reverse contrast and BH verified. Stored log2FC maximum absolute difference 5.33e-15.
- GSE132741: 14,494 fitted genes, 15 libraries; integer fitted counts, reverse contrast and BH verified. Stored log2FC maximum absolute difference 5.33e-15.
- GSE284723: 15,009 fitted genes, 9 libraries; integer fitted counts, reverse contrast and BH verified. Stored log2FC maximum absolute difference 5.33e-15.

Separate control-reference `~condition` fits, median-ratio size factors, parametric dispersions, Wald tests, BH and independent filtering at alpha=0.05. DEGs require padj<0.05 and |unshrunken log2FC|>1: post hoc effect selection, not a nonzero-null significance test. apeglm effects remain separate from original p-values. R 4.4.3, DESeq2 1.46.0, apeglm 1.28.0 and jsonlite 2.0.0.

Default external replacement affects 1,243 genes; a complete no-replacement fit exists. Third groups 5/4 do not meet default replacement eligibility (7). Five third-study genes have Cook-excluded p-values; disabling Cook exclusion is diagnostic only. PCA is recomputed from stored fitted objects using VST blind=False, top 500 variable genes; percentages/distances are exported. Per-library retained-gene count totals, size factors, median/max Cook values are in `qc/*_samples.csv`; these totals are not total sequenced reads. PCA cannot certify animal independence, eliminate cell-mixture/batch confounding or prove causality. No sample was excluded for improving results.

**Continuous-covariate caveat:** DESeq2 does not automatically filter/replace Cook outliers for continuous designs [9]. Fasting-adjusted inference has 14,494 valid adjusted p-values versus 13,252 in the unadjusted no-replacement fit. Therefore 2,958 adjusted DEGs versus 2,019 unadjusted no-replacement DEGs reflects changed outlier eligibility as well as model estimates. The adjusted discovery overlap is 974 (956 concordant, 18 discordant). It is diagnostic, not a clean causal measure of fasting confounding. Fixed-universe comparisons are exported; the 555 context-supported candidates are already required to pass unadjusted Cook-filtered no-replacement criteria.

## Concordance and Selection Bias

| study_a | study_b | subset | genes | sign_concordance | marginal_sign_expectation | pearson_r | spearman_rho |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GSE156496 | GSE132741 | all_common_finite_effects | 12815 | 0.752868 | 0.499779 | 0.765091 | 0.685188 |
| GSE156496 | GSE132741 | DEG_intersection | 976 | 0.996926 | 0.862466 | 0.843744 | 0.722734 |
| GSE156496 | GSE284723 | all_common_finite_effects | 13664 | 0.706821 | 0.49987 | 0.761198 | 0.618918 |
| GSE156496 | GSE284723 | DEG_intersection | 870 | 0.997701 | 0.810868 | 0.873269 | 0.758705 |
| GSE132741 | GSE284723 | all_common_finite_effects | 12980 | 0.660092 | 0.501416 | 0.658851 | 0.511896 |
| GSE132741 | GSE284723 | DEG_intersection | 909 | 0.984598 | 0.795624 | 0.824754 | 0.695303 |

Discovery/mdx sign agreement rises from 75.29% across all finite common effects to 99.69% in overlapping DEGs, approximately 24.4 percentage points of selection-associated increase. Its DEG-intersection marginal sign expectation is 86.25%, versus approximately 50% across all common genes. Strong shared injury/regeneration/immune responses are plausible; selecting two significant large effects and bulk composition changes also raise agreement. These sources cannot be apportioned causally by this analysis. Marginal expectation is descriptive, not a valid dependent-gene null test. All-gene correlations and a fixed eligible universe across setting alternatives are provided to expose, not erase, selection effects.

## Overlap, Pathways and Sensitivity

| study_a | study_b | universe | overlap | concordant | discordant | overlap_log10_p |
| --- | --- | --- | --- | --- | --- | --- |
| GSE156496 | GSE132741 | 12814 | 976 | 973 | 3 | -592.485 |
| GSE156496 | GSE284723 | 13659 | 870 | 868 | 2 | -570.219 |
| GSE132741 | GSE284723 | 12976 | 909 | 895 | 14 | -485.931 |

Hypergeometric log-survival values avoid numerical zero probabilities. Pair-specific common nonmissing-FDR genes define the universe, not all mouse genes. Exchangeability assumptions omit correlated genes and downstream exploratory multiplicity. No pooled effect or meta-analysis is justified by the available heterogeneous contexts.

| study_a | study_b | shared_tested_terms | shared_enriched_terms |
| --- | --- | --- | --- |
| GSE132741 | GSE284723 | 671 | 29 |
| GSE156496 | GSE132741 | 673 | 30 |
| GSE156496 | GSE284723 | 667 | 34 |

Reactome v95 uses separately mapped valid-FDR backgrounds. All terms with 10-500 background genes, including zero-overlap terms, enter one-sided hypergeometric/BH families separately for all/up/down. Common-three-study-background enrichment is a separate sensitivity analysis. Coverage and universe sizes are exported.

There are 108 threshold/context/outlier/filter setting rows across three study pairs; overlap ranges 410-2192 across different universes, not a confidence interval. Third filtering >=20 in >=3 yields 1,490 DEGs; >=10 in >=4 yields 1,669, versus default 1,817. Fasting-adjusted external fit yields 2958 DEGs without replacement. Discovery/mdx overlap falls 976 to 896 with replacement disabled. 572 candidates pass all specified three-study/default/no-replacement/third-filter criteria; 555 also pass context adjustment. No new primary filtering refit grid; leave-pair-out expression perturbations do not substitute for significance refits.

## STRING Association Network

Mouse taxon 10090, STRING v12.0: 1,408 uniquely mapped discovery DEGs of 1,499; 17,872 unique undirected non-self associations >=0.4; 4,646 associations >=0.7. Endpoints, scores, seven evidence channels, raw hashes, degree handshake and normalized PageRank are checked by integrity tests. Degree normalization uses n-1. Unweighted betweenness approximates 64 seeded pivots; PageRank and Louvain use confidence weights, with seed 156496. Isolates remain in full graphs. Communities are algorithm-dependent, not independently measured biology. Cached versioned responses, not live updated predictions, are the source; no additional neighbor genes. Display-selected hubs and DEG-induced graphs cannot establish disease specificity. Associations are not causality or necessarily physical binding.

## Candidate Formula Audit

Equation: `score = sum(w_j * component_j * available_j) / sum(w_j)`. Balanced weights: statistical .25, effect .20, consistency .15, pathway .10, network .10, replication .20. Missing components stay NA and contribute zero with a fixed preset denominator. Connectivity cannot exceed 10% in balanced scoring; omission presets renormalize by their own fixed weight sum.

- statistical: min(-log10(discovery BH padj)/20,1)
- effect: min(abs(apeglm log2FC)/3,1)
- consistency: Fraction of 9 normalized D51-versus-WT sample pairs whose direction agrees with DESeq2
- pathway: Maximum min(-log10(pathway BH padj)/5,1) for all-DEG enriched Reactome terms containing the gene
- network: log(1+degree)/log(1+maximum degree), full STRING DEG-induced network at confidence 0.7
- replication: Direction agreement * min(-log10(external BH padj)/10,1) * min(abs(external unshrunken log2FC)/2,1)

Nine pairwise normalized sample comparisons and nine leave-pair-out mean-ratio perturbations (+1 pseudocount) are descriptive, not independently repeated experiments. First three columns must be WT and last three D51, checked against metadata in tests. Five presets, two network thresholds and no-replacement setting give eight rank scenarios. Ties use gene ID, not a biological preference. Third-study evidence is separate from preserved scores, preventing retrospective score inflation. Evidence includes effects, SE, FDR, sign, pathways, centrality and sensitivity for every discovery candidate. Correlated heuristic evidence is not calibrated probability.

## Reproduction and Software Status

Prior Phase 3 isolated raw-input discovery rerun matched eight numeric tables exactly (rtol=1e-8, atol=1e-10); record preserved and input hashes rechecked. Current fitted objects reproduce log2FC within 5.33e-15 and verify reverse contrasts/BH. Third default and two filter fits and external fasting-context fit executed. External studies have not been independently reproduced in a second environment. Docker executable absent, recipe untested. Clean-extraction tests verify software/artifacts, not independent experimental replication. Actual current software outcomes are recorded separately in `results/validation/final_validation.json`; do not substitute Phase 3 outcomes for Phase 4 validation.

## Limitations

- Sex not explicitly documented in GEO sample fields; sex effects cannot be ruled out.
- Genotype, age, conditional deletion, fasting context and genome annotation differ.
- Third cohort has nine submitted libraries and no explicit individual-animal IDs; biological independence follows reported design, not independent verification.
- Continuous fasting covariate disables automatic Cook filtering: adjusted/unadjusted no-replacement FDR coverage differs. Adjustment is diagnostic, not proof of confounder removal.
- Counts reanalyzed, not raw FASTQ realignment. Reactome background excludes unmapped identifiers.
- STRING edges are associations, not causal regulation; DEG selection biases connectivity.
- Candidate weights are heuristic; correlated evidence and discovery selection prevent calibrated probability interpretation.
- No meta-analysis: three heterogeneous model contexts, conditional-control comparator not WT, limited variance/cohort covariates.
- Third-cohort publication already compares earlier dystrophin datasets; do not claim first biological discovery.

## References

1. [GEO GSE156496](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156496); [Degenerative and regenerative pathways underlying Duchenne muscular dystrophy revealed by single-nucleus RNA sequencing](https://pubmed.ncbi.nlm.nih.gov/33148801/). This reanalysis uses deposited bulk-muscle counts.
2. [GEO GSE132741](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE132741); [Peripheral blood transcriptome profiling enables monitoring disease progression in dystrophic mice and patients](https://pubmed.ncbi.nlm.nih.gov/33751844/). Only the mouse TA subset is analyzed here.
3. [GEO GSE284723](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE284723); [Karuppasamy et al. Conditional Dmd ablation in muscle and brain causes profound effects on muscle function and neurobehavior. Communications Biology (2025)](https://doi.org/10.1038/s42003-025-09128-y).
4. [Love, Huber and Anders. Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. Genome Biology (2014)](https://doi.org/10.1186/s13059-014-0550-8).
5. [Zhu, Ibrahim and Love. Heavy-tailed prior distributions for sequence count data: removing the noise and preserving large differences. Bioinformatics](https://doi.org/10.1093/bioinformatics/bty895).
6. [Reactome release 95 Ensembl mapping](https://download.reactome.org/95/Ensembl2Reactome.txt). Release-pinned mouse subset and original source hashes are bundled.
7. [STRING database in 2023: protein-protein association networks and functional enrichment analyses for any sequenced genome of interest](https://pubmed.ncbi.nlm.nih.gov/36370105/); [official score documentation](https://string-db.org/help/scores/).
8. Reviewed exclusions: [GSE126416](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE126416), [GSE262341](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE262341), [GSE324363](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE324363). Cached official matrices accompany the evidence review.
9. [Official DESeq2 vignette, count-outlier handling](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html). Continuous-covariate behavior also verified in the installed DESeq2 1.46.0 vignette.

# Phase 5 Addendum

The Phase 4 audit below is preserved. The final audit is `FINAL_SCIENTIFIC_AUDIT.md`. Phase 5 reconstructed all three inputs and reran the original R scripts in isolation; 24 CSV tables matched with maximum numerical difference zero (rtol 1e-8, atol 1e-10). This includes external no replacement and both third count-filter alternatives. Original 204 scientific files were unchanged. Same host/R installation, not independent analyst or second-R-environment validation; the context-adjusted fit and FASTQ alignment were not newly rerun. Machine evidence: `results/validation/phase5/reproduction.json`; current tests: `results/validation/phase5/tests.json`.
