# Candidate Gene Evidence

Generated 2026-10-11T18:09:01.302750+00:00. Exploratory gene hypotheses, not validated diagnostic or therapeutic biomarkers.

## Explainable Evidence

Population: all 1,499 discovery DEGs. Original ranks were frozen before third-study evidence; third effects were not used to increase scores. Full per-study unshrunken/apeglm effects, SE, FDR, directions, missingness, pathway IDs, STRING metrics and alternative-fit flags: `results/phase4/candidate_evidence.csv`. Interactive comparison permits four candidates; forest intervals are approximate within-study log2FC +/-1.96 SE, not pooled estimates or selection-corrected intervals.

| gene_symbol | gene_id | rank_balanced | score_balanced | GSE156496_log2FoldChange | GSE132741_log2FoldChange | GSE284723_log2FoldChange | sensitivity_rank_min | sensitivity_rank_max | three_study_filter_outlier_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Itgax | ENSMUSG00000030789 | 1 | 0.985266 | 4.81345 | 4.37717 | 4.88731 | 1 | 10 | True |
| Tyrobp | ENSMUSG00000030579 | 2 | 0.981888 | 3.67851 | 2.9035 | 2.98124 | 2 | 9 | True |
| Itgb2 | ENSMUSG00000000290 | 3 | 0.979111 | 3.62484 | 2.88453 | 3.50536 | 1 | 4 | True |
| Cd68 | ENSMUSG00000018774 | 4 | 0.976605 | 4.08102 | 2.38037 | 3.40311 | 1 | 9 | True |
| Trem2 | ENSMUSG00000023992 | 5 | 0.973005 | 5.32023 | 5.06629 | 5.01795 | 4 | 6 | True |
| Cybb | ENSMUSG00000015340 | 6 | 0.965633 | 3.38408 | 2.68426 | 3.20206 | 2 | 9 | True |
| Serpinb1a | ENSMUSG00000044734 | 7 | 0.952535 | 3.2415 | 3.8841 | 4.02357 | 7 | 17 | True |
| Hk3 | ENSMUSG00000025877 | 8 | 0.948139 | 3.53992 | 3.179 | 3.97225 | 6 | 16 | True |
| C3ar1 | ENSMUSG00000040552 | 9 | 0.948139 | 3.87852 | 2.84482 | 3.61123 | 8 | 17 | True |
| Tubb2b | ENSMUSG00000045136 | 10 | 0.939256 | 3.48879 | 3.82886 | 1.34014 | 7 | 24 | True |

## Equations and Missingness

`S = sum(w_j * c_j * available_j) / sum(w_j)`. Each component is bounded [0,1]; missing is NA, contributes no confirmed support and never removes its preset denominator weight. Missing is not negative biological evidence. Deterministic ties use ascending gene ID and do not indicate biological preference.

| Component | Balanced weight | Definition |
| --- | --- | --- |
| statistical | 0.25 | min(-log10(discovery BH padj)/20,1) |
| effect | 0.2 | min(abs(apeglm log2FC)/3,1) |
| consistency | 0.15 | Fraction of 9 normalized D51-versus-WT sample pairs whose direction agrees with DESeq2 |
| pathway | 0.1 | Maximum min(-log10(pathway BH padj)/5,1) for all-DEG enriched Reactome terms containing the gene |
| network | 0.1 | log(1+degree)/log(1+maximum degree), full STRING DEG-induced network at confidence 0.7 |
| replication | 0.2 | Direction agreement * min(-log10(external BH padj)/10,1) * min(abs(external unshrunken log2FC)/2,1) |

Statistical caps may saturate; pathway/STRING/statistical support is dependent and affected by discovery selection and literature bias. A 10% network cap does not prove rank insensitivity to degree. The nine sample pairs are not nine independent biological replicates; consistency is descriptive. Leave-pair-out effects use normalized means and pseudocount one, not refitted DESeq2 significance.

## Robustness

| scenario | top50_overlap_with_balanced | rank_spearman_with_balanced |
| --- | --- | --- |
| balanced | 50 | 1 |
| statistics | 32 | 0.960509 |
| replication | 46 | 0.931804 |
| no_network | 39 | 0.986321 |
| no_pathway | 38 | 0.974801 |
| network_40 | 45 | 0.995563 |
| network_90 | 44 | 0.996248 |
| no_replacement | 49 | 0.988153 |

572 genes are concordant DEGs in three default fits plus external no replacement and two third count filters. 555 also retain diagnostic measured-fasting support; automatic Cook filtering differs in that fit. Neither count means stable at every FDR/effect cutoff. No-network top-50 overlap 39/50; no-pathway 38/50. Examples Itgax, Tyrobp, Itgb2, Cd68 and Trem2 are selected by original heuristic ranking, not independently validated discoveries. Bulk cell composition may contribute; no claim of cell-intrinsic pathogenicity follows.

## Verification and Limits

Executed component/rank/stability checks: `tests/test_phase4.py`, `tests/test_phase5.py`, current log `results/validation/phase5/python.log`. Use `python -m unittest discover -s tests -v`. Same-host full R reruns reproduce the input statistics, not the clinical utility of a score. Scores are not probabilities and no training/held-out accuracy, wet-lab perturbation or human outcome model was performed. Weight sensitivity is descriptive, not a confidence interval. Follow-up requires prespecified candidates, matched independent cohorts and functional evidence.
