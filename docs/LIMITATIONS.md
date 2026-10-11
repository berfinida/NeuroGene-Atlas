# Limitations

## Publication Restriction

GSE284723's ten planned, nine deposited and eight article-described samples remain unexplained after original workbook/GEO alignment, current BioSample and Figshare review. Third-study findings and three-study stability counts are exploratory only and excluded from validated headline evidence. No new refit or sample deletion is justified. See `docs/GSE284723_SAMPLE_AUDIT.md`. Raw-inclusive research redistribution and hosted CI remain pending; source-only CI does not certify the full scientific dataset.

## Phase 5 Update

Three isolated original-input R reruns now reproduced 24 stored CSV tables, including external no replacement and third filter alternatives; historical statements below that an external full rerun was not performed describe earlier phases. The existing same-host R installation was reused, so an independent analyst/second R environment is still unavailable. Context fit/FASTQ alignment not newly rerun. Current consolidated limits: `FINAL_SCIENTIFIC_AUDIT.md` and `PUBLICATION_READINESS.md`. Dataset/QC switch all three studies; primary DE/expression/pathway tools remain discovery-specific, and volcano/MA are static unshrunken figures. No full WCAG, multi-browser, real-device or public security certification.

- DESeq2 executed and discovery independently reproduced in Conda macOS ARM64. Docker recipe supplied but untested. External default/sensitivity fits completed; a second isolated external full rerun was not performed.
- `results/GSE156496/exploratory_de_not_deseq2.csv` is not a final differential expression result. It is an exploratory smoke-test table generated from log-normalized counts.
- The dataset has three biological replicates per condition and is mouse-derived; candidate biomarker claims require independent validation and should not be framed as clinical evidence.
- Two external mouse model cohorts, not matched replications: genotype, age (1 month, 30 weeks, 4-6 months), workflow and bulk-cell mixtures limit inference. Sex is not explicitly supplied in GEO sample fields. No pooled analysis, human outcomes, clinical validation or causal claims.
- GSE284723 deposits 5 controls/4 cases despite design prose claiming 5/group and a publication legend reporting 4/group. All submitted libraries retained; no unsupported sample exclusion. Per-animal identity is not independently verified for discovery/third cohorts. Floxed controls are not WT; conditional-model molecular effects are not interchangeable with constitutive mdx/D51.
- GRCm39/Gencode M32 versus mm10 annotation differences are not reconciled by stable IDs alone. Only original counts were reanalyzed; FASTQ alignment was not reproduced.
- DEG-intersection selection inflates agreement: discovery/mdx 75.3% over common finite effects versus 99.7% in overlapping DEGs. Marginal-sign expectation, overlap p-values and threshold robustness do not resolve bulk-cell mixtures or correlated-gene uncertainty.
- Fasting-adjusted external model is exploratory: measured duration may be mediator/proxy, clock times interpreted as same-day; no complete collection-time/batch adjustment. Primary filter-refit grid was not expanded. Forest intervals are within-study approximate Wald intervals, not pooled estimates.
- DESeq2 automatic Cook filtering is not applied with the continuous fasting covariate. Valid-FDR coverage is 14,494 adjusted versus 13,252 unadjusted without replacement; DEG-count differences cannot be attributed solely to fasting. The 555 context-supported candidates are already restricted by unadjusted no-replacement evidence.
- External default replacement affects 1,243 genes; no-replacement changes valid-inference coverage. Sensitivity settings are not confidence intervals.
- Exact unique symbol mapping excludes 1,037 external symbols; 91 discovery DEGs lack STRING mapping. Missing evidence is explicit.
- ORA depends on DEG cutoffs and annotation coverage; separate BH families do not adjust all downstream exploratory multiplicity. Pathways and network evidence are correlated with discovery selection.
- STRING includes indirect/predicted/text-mined associations, not necessarily physical interactions. Publication and DEG-selection bias affect metrics; betweenness is approximate, communities algorithm-dependent.
- Candidate weights/caps are heuristics; rank changes across eight settings are displayed. Scores are not probabilities; leave-pair-out mean perturbation is not repeated DESeq2 testing.
- Browser coverage is Chromium desktop/mobile emulation, not Safari/Firefox, real mobile devices or complete assistive-technology audit. No authentication/public-production hardening.
- Historical Phase A files describe the earlier environment without R; preserved for traceability. Current final results live under results/*/deseq2/.
- The conditional-model paper already compared earlier dystrophin data; platform improvements/reanalysis should not be presented as first biological discovery. Manuscript is a draft for investigator review, not a submitted or peer-reviewed result.
