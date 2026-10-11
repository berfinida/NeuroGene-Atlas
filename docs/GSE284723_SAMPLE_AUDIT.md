# GSE284723 Sample Audit

## Decision

**Unresolved. Exclude third-study-dependent findings from validated headline evidence.** Preserve all exploratory tables, figures and nine-library DESeq2 fits. Do not silently discard a control to imitate the article or invent a fifth mKO library.

## Evidence

- Original GEO series design says five mice per group: ten expected animals.
- Cached original matrix lists GSM8691269–GSM8691277: nine unique libraries, five `Dmd flox52/Y` controls and four `Dmd flox52/Y: HSA mKO` libraries, all TA, 4–6 months.
- The original `raw counts` workbook has nine sample columns. Each is matched one-to-one, in order, to prepared metadata and GEO titles. Its 57,015 rows include 57,010 genes and five excluded HTSeq summary rows, not excluded samples.
- [Karuppasamy et al., Figure 4](https://pmc.ncbi.nlm.nih.gov/articles/PMC12673120/) describes four mice per cohort. Article methods do not identify a control library exclusion or a missing mKO library.
- Controls: `cren781`, `cren784`, `cren970`, `cren972`, `cren973`. Cases: `Crep1`, `Crep2`, `Crep3`, `Crep5`. The absent `Crep4` name is a clue, **not evidence** of a failed experiment, exclusion, missing animal or its cause.
- The matrix links nine unique BioSamples (SAMN45897314–SAMN45897322) and nine SRA experiments (SRX27130611–SRX27130619). Unique archive identifiers alone do not establish animal-level independence.
- No explicit individual-animal identifier, sex field or RNA-seq exclusion reason is available in the cached metadata. `/Y` genotype nomenclature is not a separately measured sex field.
- Reviewed preparation and R scripts retain all nine columns with design `~ condition`, Control reference and positive mKO effect. Prior Phase 5 R execution logs reproduce the stored tables exactly; no sample removal occurred in that rerun.

The article describes 1,804 DEGs whereas this documented nine-library/default-filter fit gives 1,817. Differences in cohort, filtering and implementation cannot be apportioned without original analysis code and exclusion records. Do not claim reproduction of the article's exact published analysis.

## Additional Checks

`scripts/audit_third_cohort.py` checked original hashes, alignment and group counts, reviewed the [original Figshare workbook](https://api.figshare.com/v2/articles/30090307), and retrieved all nine current BioSample XML records successfully. BioSample attributes provide no animal identifier or exclusion explanation; collection dates are missing. The Figshare workbook contains 15 physiological/behavioral worksheets, none for Figure 4 RNA-seq, and no matching RNA-seq exclusion information. Outputs are recorded in `results/validation/github/cohort/`; these are audit evidence, not new statistical fits. Supplement/reporting-summary browser downloads failed during this audit and are not claimed reviewed.

## Restrictions And Next Evidence Needed

Third-study DEGs, overlaps, pathways and the 572/555 stability subsets remain available only as exploratory conditional evidence. The frozen two-study candidate scoring and discovery/mdx comparison are unaffected. Computational reproduction validates implementation consistency, not cohort completeness or clinical utility.

Request from depositors: original animal-to-GSM/BioSample mapping; whether RNA/library QC removed an animal; why ten planned mice yielded nine deposited libraries; which eight libraries underpin Figure 4; and original count-filter/software settings. No author contact or clarification has been claimed. Until those records exist, the exact cause remains unknown and no scientifically justified corrective refit is possible.
