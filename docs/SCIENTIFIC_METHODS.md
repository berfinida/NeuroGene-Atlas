# Scientific Methods

## 0.5.1 Publication Scope

No statistical model, sample selection or numeric table was changed during GitHub preparation. The unresolved GSE284723 10/9/8 cohort counts restrict third-study inference to exploratory evidence, not validated headline results. Original Phase 5 computational reproduction remains distinct from biological/clinical validation. Only the web runtime was security-updated (FastAPI 0.143.0 / Starlette 1.3.1); R and numerical package versions for the scientific fits remain those recorded in the original sessions. Source-only fixtures test software behavior and are never research outputs.

## Phase 5 Reproduction Audit

The original three study scripts were copied with cached source inputs into an isolated temporary root. Discovery metadata/counts were reconstructed directly from official GEO files; external unique-symbol bridging and third workbook/version stripping were rerun from originals. Prepared matrices and metadata were compared to stored inputs, then R default/no-replacement/filter fits executed without overwriting results. All 24 generated shared CSVs were compared with rtol 1e-8/atol 1e-10, observed max numeric difference zero; summary fields/package versions and 204 preserved file hashes were verified. Context-adjusted fit not rerun. Same host/pinned R installation, not second-environment replication. Commands and limitations: `results/validation/phase5/reproduction.json`. Separate Phase 5 tests reconstruct all-common and selected concordance/correlations, fixed score denominators and rank tie order, and verify prepared versus fitted library counts. No scientific thresholds or ranking scores were changed.

## Phase 4 Study-Aware Analysis

See the formal root-level `SCIENTIFIC_AUDIT_REPORT.md` and source tables under `results/phase4/`. Discovery age is one month in original GEO. Sex is not explicit in the sample fields. Third cohort GSE284723 is conditional myofiber Dmd loss versus floxed controls, not mdx versus WT: 5 controls/4 cases, 4-6 months. Nine deposited libraries are retained despite ten-library design prose and a four-per-group published figure legend; no unsupported exclusion.

Third supplied HTSeq counts are integers. Exclude five `__` summary rows; strip terminal Ensembl version suffixes without aliases, aggregation or duplicates. GRCm39/Gencode M32 versus mm10 annotation differences remain. Separate DESeq2 ~condition, Control reference; default >=10 counts in >=3 samples, alternatives >=20 in >=3 and >=10 in >=4; Cook-disabled inference diagnostic only. apeglm is separate. External context fit uses ~fasting_hours_centered+condition, no replacement, measured GEO times assumed same-day; fasting may be mediator/proxy rather than an appropriate causal confounder.

All-common-finite-effect concordance is reported separately from valid-FDR and selected DEG intersections. Hypergeometric log-survival probabilities use common valid-FDR universes and omit inter-gene dependence; marginal-sign expectation is descriptive. Fixed-universe comparisons isolate some eligibility effects. Separate study-specific Reactome families and common-three-study annotation-background sensitivity are exported. No pooled effect/meta-analysis. Primary count-filter refit grid was not expanded.

Continuous fasting covariate disables DESeq2 automatic Cook filtering/replacement, as verified in the installed vignette. Adjusted valid-FDR coverage is 14,494 versus 13,252 unadjusted without replacement; DEG counts are not a pure paired estimate of fasting effects. Context-supported candidates are additionally required to pass unadjusted no-replacement inference.

Preserved Phase 3 scores are not retrospectively increased by third-study data. Evidence profiles add per-study raw/shrunken effects, SE, FDR, direction, pathways, STRING metrics and alternative-fit stability. Three-study stable criteria require concordant DEGs in three defaults, external no replacement and two third filters (572 genes); fasting-adjustment support is separate (555). Wald intervals are approximate within-study log2FC +/-1.96*SE, not pooled/heterogeneity-adjusted. Publication figures and complete captions/source/parameters: `results/publication/figure_manifest.json`.

## Phase A

The raw count matrix is read from the official GEO supplementary count table. Counts are validated as non-negative integers, with six configured sample columns mapped to GEO sample accessions through the official series matrix.

Low-count filtering currently keeps genes with at least 10 counts in at least three samples. For local QC, size factors are estimated with the median-ratio method, followed by log2(size-factor-normalized count + 1) transformation for PCA, sample distances, and correlations.

## Final Differential Expression

Final differential expression analysis is implemented in `scripts/rna_seq/deseq2_gse156496.R`:

- raw integer counts as input
- design formula `~ condition`
- reference group `WT`
- contrast `D51` versus `WT`
- Benjamini-Hochberg adjusted p-values from DESeq2
- separate completed apeglm effect-size shrinkage with original p-values retained

Executed with R 4.4.3, DESeq2 1.46.0, apeglm 1.28.0 and jsonlite 2.0.0. Median-ratio normalization, parametric dispersion, Wald testing, BH adjustment, independent filtering and default Cook's cutoff. Positive effects mean higher mutant expression. DEGs: padj <0.05 and |unshrunken log2FC| >1; post hoc cutoff, not a nonzero-null test. VST blind=FALSE, top-500-variable PCA, top-30-padj heatmap, Euclidean sample distances. Historical Python log-count statistics are separate, never final inference.

## Independent Evaluation

GSE132741: only GEO-labelled 30-week mouse bulk tibialis anterior, 7 WT / 8 mdx, 15 unique animals. Exclude blood, longitudinal blood, utrophin genotypes and four younger TA samples. Primary article describes HTSeq-count; GEO processing text mentions Cufflinks. Supplied counts are integers with HTSeq summary rows removed, never rounded.

Exact case-sensitive unique symbols map against discovery mm10 annotations: 23,414 retained of 24,451, 1,037 unresolved/ambiguous excluded; no alias guessing. Separate DESeq2 ~condition WT-reference fits. Default minReplicatesForReplace=7 replaced counts in 1,243 genes; second complete fit uses Inf. No pooling. Genotype (exon 51 versus exon 23), age (one-month discovery versus 30-week external), lab and workflow differ. Phase 4 corrected the age from original GEO sample fields; numerical outputs are unchanged.

Shared inference requires valid padj in both datasets. Report overlap/Jaccard, concordant/discordant directions, hypergeometric overlap, Pearson/Spearman unshrunken effects, median absolute effect difference and pathway overlap. Extremely small p-values may underflow to zero; not exact-zero probability. Eighteen sensitivity settings: FDR 0.01/0.05/0.1 x |LFC| 0.5/1/1.5 x default/no replacement. Universes change with outlier settings; perturbations are not confidence intervals.

## Reactome and STRING

Reactome release 95 mouse mapping. Separate dataset/setting valid-padj, annotated backgrounds. Discovery: 6,893 mapped of 14,358 eligible. One-sided hypergeometric ORA on terms of 10-500 background genes, including zero-overlap terms; BH over full tested families separately for all/up/down. Compare pathway IDs without pooling backgrounds.

STRING version 12.0 API, species 10090, unique Ensembl mapping, add_nodes=0; 1,408 of 1,499 discovery DEGs mapped, 17,872 unique non-self undirected associations >=0.4. Combined/component scores in [0,1]. Associations are not causality or necessarily physical interaction; confidence is not strength.

Full graph metrics include isolates: degree, degree/(n-1), normalized unweighted betweenness approximated with 64 seeded pivots, confidence-weighted PageRank, confidence-weighted Louvain communities (seed 156496). Display capped at 200 nodes; full CSV exports unaffected. Six community colors repeat, numerical community IDs disambiguate. Cached raw responses/evidence channels are preserved.

## Exploratory Candidate Scores

Ranks use descending score then ascending Ensembl ID for deterministic ties. Equal scores do not support a biological preference within the tie; rounded displayed scores can also appear equal. Exported precision and sensitivity ranges matter more than small rank differences.

Population: 1,499 discovery DEGs. S=sum(w_j * component_j * available_j)/sum(w_j). Components bounded [0,1]; fixed denominator per preset. Missing evidence remains NA and adds no confirmed support, never raises scores by dropping denominator weight. Missing is not negative biological evidence.

| Component | Balanced weight | Definition |
| --- | --- | --- |
| Statistical | 0.25 | min(-log10(discovery padj)/20,1) |
| Effect | 0.20 | min(abs(apeglm LFC)/3,1) |
| Consistency | 0.15 | Fraction of nine normalized case/control pairs matching DESeq2 sign |
| Pathway | 0.10 | Best enriched all-DEG term min(-log10(BH padj)/5,1) containing gene |
| Network | 0.10 | log(1+degree)/log(1+max degree), confidence 0.7 |
| Replication | 0.20 | direction agreement x min(-log10(external padj)/10,1) x min(abs(external LFC)/2,1) |

Connectivity contributes at most 10% balanced score. Eight sensitivity scenarios: five weights (balanced/statistics/replication/no network/no pathway), confidence 0.4/0.9, no external replacement. Removal presets normalize by their fixed preset sums. Full rank ranges and top-50 fractions exported. Robust replicated DEG requires both external settings and matching direction. Nine leave-one-WT/one-case-out normalized mean-ratio perturbations (+1 pseudocount) assess effect stability, not repeated DESeq2 significance. DEG threshold sensitivity is reported separately. Every ranking has exported components, availability, weights and equations. Heuristic, dependent evidence is not calibrated biomarker probability.
