# Publication Readiness

Generated 2026-10-11T18:09:01.302750+00:00. Assessment: **computational draft suitable for scientific coauthor review; not unconditional submission-ready or experimentally validated**.

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
