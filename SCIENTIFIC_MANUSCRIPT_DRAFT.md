# Study-Aware Reanalysis of Dystrophin-Deficient Mouse Muscle: Cross-Model Evidence, Selection Bias and Exploratory Candidate Prioritization

Manuscript draft for author review. Computational reanalysis only; author list, affiliations, contributions, funding and ethics declarations require investigator confirmation. No new experiments were performed.

## Structured Abstract

### Background
Public mouse-muscle transcriptomes can assess reproducibility of dystrophin-loss responses, but highly concordant selected genes may conceal selection bias and heterogeneous model contexts.

### Methods
Three deposited integer-count datasets were analyzed using separate DESeq2 models. Unique identifiers harmonized genes without pooling counts. Concordance was evaluated over all commonly tested finite effects and DEG intersections. Reactome and STRING provided contextual evidence. Thresholds, outlier handling, count filtering, measured fasting duration and scoring weights were perturbed; candidate evidence was separated from ranking.

### Results
Discovery tested 14,359 genes and identified 1,499 DEGs. GSE132741 tested 14,494 genes (2,419 default DEGs; 2,019 without replacement). GSE284723 tested 15,009 genes and identified 1,817 DEGs. Discovery overlaps were 976 with mdx and 870 with conditional mKO, including 973 and 868 concordant directions. Across three default fits, external replacement disabled and both third-study count-filter alternatives, 572 discovery candidates were concordant DEGs; 555 also retained support after measured fasting-duration adjustment. These are exploratory mouse findings, not clinical validation. Discovery-mdx agreement was 75.3% across all common finite effects but 99.7% among overlapping DEGs; discovery-conditional agreement was 70.7% versus 99.8%.

### Conclusions
The platform supports auditable, exploratory cross-model mouse research. Shared effects and heuristic candidate stability are not equivalent to causal mechanism, human diagnostic discrimination or therapeutic validation.

## Introduction

Dystrophin deficiency disrupts muscle homeostasis across distinct models. GSE156496, GSE132741 and GSE284723 differ in genotype, age and processing [1-3]. Bulk muscle data cannot distinguish cell-intrinsic effects from changing immune, stromal or regenerating-cell proportions without additional analysis. Study-aware comparisons should therefore quantify common expression patterns while retaining their biological context.

NeuroGene Atlas is a reproducible evidence platform, not a trained biomarker predictor. This work asks whether effects agree beyond selected DEG intersections, how analytical choices change overlap, and which discovery candidates retain support across mouse models. The conditional-model publication already compares cytokine/extracellular-matrix signals with earlier dystrophin data [3]; we claim transparent reanalysis and robustness assessment, not first discovery of those processes.

## Materials and Methods

### Cohort Selection

| accession | age | groups | case | reference | genome |
| --- | --- | --- | --- | --- | --- |
| GSE156496 | 1 month | 3 WT / 3 D51 | D51 (exon 51 deletion) | WT | mm10 |
| GSE132741 | 30 weeks | 7 WT / 8 mdx | mdx | WT | mm10 symbol bridge |
| GSE284723 | 4-6 months | 5 controls / 4 mKO | Dmd flox52/Y: HSA mKO | Dmd flox52/Y (not WT) | GRCm39 Gencode M32 |

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

### Final Reproduction Audit (Phase 5)

All three deposited count inputs were reconstructed in an isolated temporary root and the original R scripts were rerun without replacing stored results. Twenty-four numerical CSV tables matched at rtol=1e-8 and atol=1e-10, with a maximum observed numerical difference of zero: eight discovery tables, six external tables including the full no-replacement fit, and ten conditional-cohort tables including both count-filter alternatives and the Cook-disabled diagnostic. Input matrices, sample metadata and recorded R/package versions also matched; 204 original scientific files remained SHA-256 unchanged. This same-host rerun used the existing R 4.4.3/DESeq2 1.46.0 installation and a newly installed Python environment. It is computational reproduction, not independent analyst/second-R-environment or biological validation. The fasting-adjusted fit and FASTQ alignment were not rerun in this final audit. Complete commands and comparisons are in `results/validation/phase5/reproduction.json`; publication qualifications are in `PUBLICATION_READINESS.md`.

### Differential Expression and Audit

Discovery tested 14,359 genes and identified 1,499 DEGs. GSE132741 tested 14,494 genes (2,419 default DEGs; 2,019 without replacement). GSE284723 tested 15,009 genes and identified 1,817 DEGs. Discovery overlaps were 976 with mdx and 870 with conditional mKO, including 973 and 868 concordant directions. Across three default fits, external replacement disabled and both third-study count-filter alternatives, 572 discovery candidates were concordant DEGs; 555 also retained support after measured fasting-duration adjustment. These are exploratory mouse findings, not clinical validation. Third filter alternatives yielded 1,490 and 1,669 DEGs; the fasting-adjusted external model yielded 2958 DEGs without replacement. Stored log2FC recomputation differences were at most 5.33e-15. Deposited/published third-sample discrepancies remain explicit; published DEG counts are not expected to be reproduced by arbitrarily dropping one control.

### Concordance and Selection

| study_a | study_b | universe | overlap | concordant | discordant | overlap_log10_p |
| --- | --- | --- | --- | --- | --- | --- |
| GSE156496 | GSE132741 | 12814 | 976 | 973 | 3 | -592.485 |
| GSE156496 | GSE284723 | 13659 | 870 | 868 | 2 | -570.219 |
| GSE132741 | GSE284723 | 12976 | 909 | 895 | 14 | -485.931 |

| study_a | study_b | subset | genes | sign_concordance | marginal_sign_expectation | pearson_r | spearman_rho |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GSE156496 | GSE132741 | all_common_finite_effects | 12815 | 0.752868 | 0.499779 | 0.765091 | 0.685188 |
| GSE156496 | GSE132741 | DEG_intersection | 976 | 0.996926 | 0.862466 | 0.843744 | 0.722734 |
| GSE156496 | GSE284723 | all_common_finite_effects | 13664 | 0.706821 | 0.49987 | 0.761198 | 0.618918 |
| GSE156496 | GSE284723 | DEG_intersection | 870 | 0.997701 | 0.810868 | 0.873269 | 0.758705 |
| GSE132741 | GSE284723 | all_common_finite_effects | 12980 | 0.660092 | 0.501416 | 0.658851 | 0.511896 |
| GSE132741 | GSE284723 | DEG_intersection | 909 | 0.984598 | 0.795624 | 0.824754 | 0.695303 |

Discovery-mdx overlap decreases to 896 with replacement disabled. All-gene Pearson correlations are 0.765 (discovery-mdx), 0.761 (discovery-conditional) and 0.659 (mdx-conditional); Spearman values are 0.685, 0.619 and 0.512. Agreement is much higher after selecting significant intersections, which also have skewed sign marginals. Thus 973/976 concordance is not an unbiased genome-wide replication rate, although broad correlations support shared expression patterns.

### Functional and Candidate Evidence

| study_a | study_b | shared_tested_terms | shared_enriched_terms |
| --- | --- | --- | --- |
| GSE132741 | GSE284723 | 671 | 29 |
| GSE156496 | GSE132741 | 673 | 30 |
| GSE156496 | GSE284723 | 667 | 34 |

Shared enriched terms use separate inferential backgrounds; common-background sensitivity exposes annotation dependence. STRING retains 1,408 genes and 17,872 associations >=0.4; 4,646 associations remain >=0.7. High-degree display selection cannot establish pathogenicity. Preserved top candidates include Itgax, Tyrobp, Itgb2, Cd68 and Trem2; forest plots show separate approximate Wald intervals. Candidate stability remains conditional on discovery selection and chosen cutoffs.

## Discussion

Distinct dystrophin-deficient models exhibit correlated muscle effects, but near-complete selected-DEG agreement is partly a property of selection. Comparing approximately 66-75% all-gene sign agreement with approximately 98-100% intersection agreement demonstrates why the tested universe must accompany replication claims. Shared injury and immune/regenerative responses are plausible, but bulk composition and unmeasured covariates can generate similar patterns. No cell-intrinsic or causal attribution follows from these comparisons.

Outlier replacement and filtering materially affect counts and overlap. Fixed-universe correlations help distinguish eligibility changes, but missingness is not random and perturbations are not uncertainty intervals. Fasting adjustment is a measured-context diagnostic, not proof that an adjusted genotype effect is biologically preferable. Collection-time effects and batch covariates remain incompletely modeled; fasting could reflect genotype-associated physiology. Stable Ensembl identifiers reduce ambiguity but do not reconcile genome annotations or upstream quantification.

DESeq2's continuous-covariate design does not apply automatic Cook filtering [9]. All 14,494 context-fit genes have valid FDR versus 13,252 in the unadjusted no-replacement fit. The 2,958/2,019 DEG comparison consequently mixes eligibility and effect changes, not solely fasting adjustment. The 555 context-supported candidates already pass the unadjusted no-replacement filter; this does not confer causal or clinical validity.

Candidate profiles prioritize inspectability over prediction. Capping network evidence limits hub dominance under balanced weights, yet pathway, statistical and network evidence remain dependent. Preserving pre-existing ranks avoids retrospective third-study score inflation, but not discovery winner's curse. Follow-up should prespecify candidates, use matched cohorts and include targeted expression/protein/functional assays; none were undertaken here. The associated publication's experimental results are not experiments performed by this project.

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

Additional limits include unresolved third deposited-versus-published sample counts, no new primary filter-refit grid, gene dependence in overlap tests, downstream exploratory multiplicity, and heuristic ranking ties. Forest intervals are within-study approximate Wald intervals, not heterogeneity-adjusted meta-analytic intervals. Human discrimination, causality, independent external second-environment reproduction and container execution remain unavailable.

## Conclusions

NeuroGene Atlas provides an auditable computational reanalysis with real study-specific effects, reproducible figures and transparent candidate evidence. Cross-model support motivates hypotheses, not clinical or causal claims. Its principal contribution is an evidence trail that makes selection and uncertainty visible.

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


## Figure Legends

**Figure 1. GSE156496 PCA.** DESeq2 variance-stabilized expression, blind=False; PCA on the 500 highest-variance genes within GSE156496. Each point is a submitted library. Percentages refer to variance of these selected features. No samples excluded; separation does not establish causality or independence. Parameters: `{"blind": false, "ntop": 500, "source": "Stored fitted dds.rds, recomputed by audit_fits.R"}`. Files: `results/publication/pca_GSE156496.pdf`, `.svg`, `.csv`.

**Figure 2. GSE156496 differential expression.** Unshrunken DESeq2 effects and BH-adjusted p-values in GSE156496. Rose: padj<0.05 and |log2FC|>1. Missing padj excluded from rendering; all tested rows remain in source CSV. Positive effects indicate D51, mdx or conditional mKO relative to its own control. P-values at zero are numerical underflow, displayed using 1e-300. Parameters: `{"fdr": 0.05, "abs_log2fc": 1, "p_floor": 1e-300, "estimate": "unshrunken"}`. Files: `results/publication/volcano_GSE156496.pdf`, `.svg`, `.csv`.

**Figure 3. GSE132741 PCA.** DESeq2 variance-stabilized expression, blind=False; PCA on the 500 highest-variance genes within GSE132741. Each point is a submitted library. Percentages refer to variance of these selected features. No samples excluded; separation does not establish causality or independence. Parameters: `{"blind": false, "ntop": 500, "source": "Stored fitted dds.rds, recomputed by audit_fits.R"}`. Files: `results/publication/pca_GSE132741.pdf`, `.svg`, `.csv`.

**Figure 4. GSE132741 differential expression.** Unshrunken DESeq2 effects and BH-adjusted p-values in GSE132741. Rose: padj<0.05 and |log2FC|>1. Missing padj excluded from rendering; all tested rows remain in source CSV. Positive effects indicate D51, mdx or conditional mKO relative to its own control. P-values at zero are numerical underflow, displayed using 1e-300. Parameters: `{"fdr": 0.05, "abs_log2fc": 1, "p_floor": 1e-300, "estimate": "unshrunken"}`. Files: `results/publication/volcano_GSE132741.pdf`, `.svg`, `.csv`.

**Figure 5. GSE284723 PCA.** DESeq2 variance-stabilized expression, blind=False; PCA on the 500 highest-variance genes within GSE284723. Each point is a submitted library. Percentages refer to variance of these selected features. No samples excluded; separation does not establish causality or independence. Parameters: `{"blind": false, "ntop": 500, "source": "Stored fitted dds.rds, recomputed by audit_fits.R"}`. Files: `results/publication/pca_GSE284723.pdf`, `.svg`, `.csv`.

**Figure 6. GSE284723 differential expression.** Unshrunken DESeq2 effects and BH-adjusted p-values in GSE284723. Rose: padj<0.05 and |log2FC|>1. Missing padj excluded from rendering; all tested rows remain in source CSV. Positive effects indicate D51, mdx or conditional mKO relative to its own control. P-values at zero are numerical underflow, displayed using 1e-300. Parameters: `{"fdr": 0.05, "abs_log2fc": 1, "p_floor": 1e-300, "estimate": "unshrunken"}`. Files: `results/publication/volcano_GSE284723.pdf`, `.svg`, `.csv`.

**Figure 7. Pairwise DEG overlap.** Pairwise DEG intersections restricted to each pair's common valid-FDR universe. Bars separate concordant and discordant effects. Universes differ by pair; these are not three-way Venn counts. Hypergeometric log10 p-values in source CSV are descriptive and do not model correlated genes. Parameters: `{"fdr": 0.05, "abs_log2fc": 1, "universe": "Pair-specific common nonmissing padj"}`. Files: `results/publication/deg_overlap.pdf`, `.svg`, `.csv`.

**Figure 8. All-gene effect concordance.** All commonly tested genes with finite unshrunken effects, regardless of significance or availability of adjusted p-values. Diagonal is identity, not a fitted model. Genotype, age and processing heterogeneity preclude interchangeability of effects. Selection-bias statistics are provided separately. Parameters: `{"selection": "No DEG selection", "estimate": "unshrunken"}`. Files: `results/publication/effect_concordance.pdf`, `.svg`, `.csv`.

**Figure 9. Study-specific candidate effects.** Five candidates selected using preserved Phase 3 balanced ranks, before adding the third study. Separate unshrunken effects with approximate Wald intervals (log2FC +/- 1.96*lfcSE). No pooled estimate. Conditional selection and small sample sizes limit interval interpretation; uncertainty is within-study, not heterogeneity-adjusted. Parameters: `{"selection": "Top five Phase 3 balanced candidates", "CI": "Approximate normal 95% Wald", "pooling": false}`. Files: `results/publication/gene_forest.pdf`, `.svg`, `.csv`.

**Figure 10. Shared Reactome enrichment.** Fifteen pair/pathway entries with the lowest study-A adjusted p-values among shared all-DEG enriched Reactome v95 terms. Repeated terms across pairs are intentional. Separate annotation-mapped valid-FDR backgrounds and BH families (10-500 background genes per term). Full shared/eligible results retained in source table; common-background sensitivity is a separate table. Parameters: `{"direction": "all", "fdr": 0.05, "term_size": [10, 500], "display_selection": "First 15 sorted by padj_a"}`. Files: `results/publication/shared_pathways.pdf`, `.svg`, `.csv`.

**Figure 11. STRING association subnetwork.** Induced display of the 40 highest-degree mapped discovery DEGs at combined confidence >=0.7. Node size uses degree in the full 1,408-node network; colors use full-graph Louvain communities. Spring positions seeded 156496. Edges are functional associations, not causal regulation; display selection favors hubs and cannot establish disease specificity. Exact displayed edges in string_network_edges.csv. Parameters: `{"confidence": 0.7, "nodes": 40, "seed": 156496, "selection": "Full graph degree; ties by gene ID"}`. Files: `results/publication/string_network.pdf`, `.svg`, `.csv`.

**Figure 12. Candidate study evidence.** Twenty candidates selected by preserved Phase 3 balanced rank. Colors show actual unshrunken per-study effects, clipped at +/-5 for display; source CSV contains complete evidence, standard errors, FDR, missingness, pathway and network metrics. Blank cells indicate unavailable effects, not zero evidence. This is evidence visualization, not calibrated biomarker performance. Parameters: `{"selection": "Top 20 preserved Phase 3 ranks", "color_limits": [-5, 5]}`. Files: `results/publication/candidate_evidence.pdf`, `.svg`, `.csv`.

**Figure 13. Threshold, outlier and count-filter sensitivity.** Pairwise overlaps at FDR<0.05 across effect cutoffs 0.5, 1 and 1.5. Alternative external count replacement and third-study count-filter fits are separate analyses; Cook-cutoff-disabled estimates are diagnostic only. Full 0.01/0.05/0.1 FDR grid in source CSV. Changes in eligible universes are reported and are not confidence intervals. Parameters: `{"fdr_display": 0.05, "fdr_grid": [0.01, 0.05, 0.1], "lfc_grid": [0.5, 1, 1.5]}`. Files: `results/publication/statistical_sensitivity.pdf`, `.svg`, `.csv`.

**Figure 14. Candidate weight robustness.** Top-50 overlap with the Phase 3 balanced ranking across five weighting presets, two network thresholds and external outlier replacement disabled. Network contribution is capped at 10% under balanced weights. Heuristic weighting perturbations are not independent experiments or probability intervals. Parameters: `{"reference": "Phase 3 balanced", "top_n": 50, "scenarios": 8}`. Files: `results/publication/ranking_sensitivity.pdf`, `.svg`, `.csv`.

## Supplementary Materials

S1: original GEO review/metadata. S2: study-specific inference/shrinkage/session outputs. S3: all-gene effects and selection audit. S4: 108 threshold/context/filter/outlier setting rows. S5: study-specific and common-background Reactome. S6: full STRING mapping/edges/metrics. S7: candidate evidence and preserved sensitivity ranks. S8: vector figures, source CSVs, captions/parameters/hashes. S9: actual software validation and clean-release manifests. Supplements are computational artifacts, not independent experiments.
