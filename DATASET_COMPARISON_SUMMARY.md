# Dataset Comparison Summary

Generated 2026-10-11T18:09:01.302750+00:00. Sources: `results/phase4/pairwise_summary.csv`, `selection_audit.csv`, `pathway_comparison.csv`, `statistical_sensitivity.csv`, original GEO metadata `results/phase4/original_sample_metadata.json`.

## Cohorts

| accession | groups | age | case | reference | genome |
| --- | --- | --- | --- | --- | --- |
| GSE156496 | 3 WT / 3 D51 | 1 month | D51 (exon 51 deletion) | WT | mm10 |
| GSE132741 | 7 WT / 8 mdx | 30 weeks | mdx | WT | mm10 symbol bridge |
| GSE284723 | 5 controls / 4 mKO | 4-6 months | Dmd flox52/Y: HSA mKO | Dmd flox52/Y (not WT) | GRCm39 Gencode M32 |

Three separate mouse bulk tibialis anterior cohorts; no pooled model. The third comparison is conditional mKO versus floxed controls, not mdx/D51 versus WT. Sex fields and individual-animal IDs are incomplete for two cohorts. Third design/deposit/legend counts (10/9/8) remain unresolved; use all deposited libraries, not a retrospectively selected subset.

## Default Comparisons

| study_a | study_b | universe | overlap | concordant | discordant | overlap_log10_p |
| --- | --- | --- | --- | --- | --- | --- |
| GSE156496 | GSE132741 | 12814 | 976 | 973 | 3 | -592.485 |
| GSE156496 | GSE284723 | 13659 | 870 | 868 | 2 | -570.219 |
| GSE132741 | GSE284723 | 12976 | 909 | 895 | 14 | -485.931 |

Universes require common nonmissing BH padj; finite-effect universes are larger (12,815 / 13,664 / 12,980). Thresholds padj<0.05, |unshrunken log2FC|>1. Log10 hypergeometric tails are descriptive and assume exchangeable genes. All-common correlations and selected agreement are distinct quantities.

| study_a | study_b | subset | genes | sign_concordance | pearson_r | spearman_rho |
| --- | --- | --- | --- | --- | --- | --- |
| GSE156496 | GSE132741 | all_common_finite_effects | 12815 | 0.752868 | 0.765091 | 0.685188 |
| GSE156496 | GSE132741 | DEG_intersection | 976 | 0.996926 | 0.843744 | 0.722734 |
| GSE156496 | GSE284723 | all_common_finite_effects | 13664 | 0.706821 | 0.761198 | 0.618918 |
| GSE156496 | GSE284723 | DEG_intersection | 870 | 0.997701 | 0.873269 | 0.758705 |
| GSE132741 | GSE284723 | all_common_finite_effects | 12980 | 0.660092 | 0.658851 | 0.511896 |
| GSE132741 | GSE284723 | DEG_intersection | 909 | 0.984598 | 0.824754 | 0.695303 |

No-replacement discovery/mdx: 11,963 shared valid-FDR genes; 896 overlapping DEGs, 893 concordant/3 discordant. Third alternatives: 13,423 fitted genes/1,490 DEGs (count20) and 14,493/1,669 (minimum4), compared with default 15,009/1,817. Fasting adjustment changes Cook eligibility, so its 2,958 DEGs are not solely an estimate of fasting confounding. 108 existing perturbation rows are exported; not every joint setting is included. The shared pathway counts 30/34/29 refer to separate backgrounds and all-DEG families, not three-way intersection counts.

## Reproduction and Uncertainty

| Study | Tables matched | Maximum numeric difference | Status |
| --- | --- | --- | --- |
| GSE156496 | 8 | 0 | passed |
| GSE132741 | 6 | 0 | passed |
| GSE284723 | 10 | 0 | passed |

Original 204 scientific files remained unchanged. Three default fits, external no-replacement and third filter/diagnostic fits were rerun in an isolated temporary root. The R environment is the same pinned installation; Python dependencies were freshly installed. Batch, age, genotype, sex, annotation and bulk composition limit interchangeability. No meta-analysis, clinical validation or causal inference. Exact commands/tolerances/versions: `results/validation/phase5/reproduction.json`; selection recalculation: `tests/test_phase5.py`. Reproducible invocation: `python scripts/final_reproduction.py --rscript Rscript`.
