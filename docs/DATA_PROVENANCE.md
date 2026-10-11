# Data Provenance

## GitHub Preparation 0.5.1

Original scientific files and historical Phase 5 ZIPs remain unchanged. New third-cohort evidence is `results/validation/github/cohort/audit.json` with original input hashes, nine-column/GSM mapping, retrieved BioSample attributes and inspected Figshare metadata. This did not establish animal independence or explain the 10/9/8 discrepancy; all third-dependent findings remain exploratory. Raw data/results are Git-ignored, and their public redistribution is pending separate approval/rights review. Current source artifacts/checksums are in `release/github/`; see `GITHUB_RELEASE_READINESS.md` and `docs/RELEASE_STRATEGY.md`.

## Final Phase 5 Reproduction

`results/validation/phase5/reproduction.json` records every original scientific-file hash, exact isolated preparation/R commands, versions, six input-table comparisons and 24 regenerated-output comparisons. Maximum numerical difference zero, rtol 1e-8/atol 1e-10; all 204 original scientific files preserved. Existing R 4.4.3/DESeq2 1.46.0/apeglm 1.28.0 installation reused; no second-environment/analyst, context-fit or FASTQ rerun. Final archives have per-member SHA manifests and an external `release/RELEASE_MANIFEST_SHA256.txt`. Source and research bundles exclude prior release ZIPs and runtime dependencies. Current-versus-historical audit evidence is kept separate under `results/validation/phase5/`.

## Phase 4

Official GEO matrices for GSE126416/GSE262341/GSE324363/GSE284723 are cached under `data/raw/`; review JSON records URLs, original sample fields, processing and SHA-256 in `results/phase4/geo_review/`. GSE126416: quadriceps RNA pooled into three WT/mdx libraries each, not 14/15 independent libraries, supplied Cufflinks expression. GSE262341: CPM, not verified raw counts. GSE324363: treatment within dystrophic mice, no disease/control contrast. These were not fitted.

GSE284723 rawCounts.xlsx SHA-256 and processed files are recorded in `data/processed/GSE284723/provenance.json`. Nine supplied libraries, five controls/four mKO, 57,010 gene rows and five excluded HTSeq summary rows. Version suffix removal has a full identifier bridge; nonnegative integers, no count rounding. Annotation GRCm39/M32, in contrast to prior mm10.

Original selected sample characteristics are exported in `results/phase4/original_sample_metadata.json`, including discovery age=1 month and measured external fasting/collection fields. No new sex or individual IDs were invented. Context derivation/fit, stored-fit QC audit, pairwise tables, evidence and mapped-background enrichment remain separate from preserved Phase 3 outputs. `audit.json` records derived table hashes; publication manifest records SVG/PDF/PNG/source CSV hashes, captions and parameters. Current root audit/manuscript describe discrepancies and verified-reference links.

## Dataset

- GEO accession: `GSE156496`
- Title: Transcriptome analysis of the TA muscles from WT and Dmd Exon 51 Knockout mice
- Organism: `Mus musculus`
- Tissue: tibialis anterior muscle
- Platform: `GPL19057`
- Source record: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156496

## Cached Files

- `data/raw/GSE156496/GSE156496_RNAseq_RawCountTable.txt.gz`
- `data/raw/GSE156496/GSE156496_series_matrix.txt.gz`

Checksums are recorded in `results/GSE156496/analysis_manifest.json`.
Current final hashes: `results/GSE156496/deseq2/provenance.json`. Raw count SHA-256 `dc54616d8555dde03645084e917f9acfae573bfbe9ca3e94ad8ce5997bf28665`; GEO matrix `69062573016ad2e328579266bea12ee2d1a24c9116815eac655cb3aae088b081`. Eight-table raw-input reproduction, tolerances, versions and prior stale-manifest discrepancies: `results/validation/reproducibility.json`. Current provenance is refreshed without hiding historical mismatches.

## Sample Mapping

| Count column | GEO accession | Condition |
| --- | --- | --- |
| WT_1 | GSM4732625 | WT |
| WT_2 | GSM4732626 | WT |
| WT_3 | GSM4732627 | WT |
| D51_4 | GSM4732628 | D51 |
| D51_5 | GSM4732629 | D51 |
| D51_6 | GSM4732630 | D51 |

The GEO series matrix reports genotype `WT` for the first three samples and `Delta 51` for the final three samples.

## Independent Dataset

[GEO GSE132741](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE132741), [primary study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8033515/). Official matrix and 15 per-sample gzipped fragments-per-gene counts cached. All raw hashes verified by tests and listed in `data/processed/GSE132741/provenance.json`; unique animals, sample selection/exclusions and exact mm10 symbol bridge exported. GEO Cufflinks versus article HTSeq-count discrepancy explicitly recorded. External complete default/no-replacement results and session are in `results/GSE132741/deseq2/`. Source eligibility review and 18 sensitivity settings under `results/discovery/replication/`; GSE162455/GSE262341 excluded for incompatible tissue/lack of raw counts.

## Annotation and Discovery

[Reactome 95](https://download.reactome.org/95/Ensembl2Reactome.txt), original multi-species SHA-256 `14f294c529e95b156a3aec274d8f404467e81b6fbd2f4ad1fad8bd7ca0504323`. Bundled 32,725-row mouse subset SHA-256 `08c5f75dfce1f2c4e3f0473504e401c0a4284106b378b33a2b193b07bb12a298`. Original 169 MB download not bundled; versioned mouse mapping included. Background/BH methods in reactome_provenance.json.

STRING 12.0 endpoint `https://version-12-0.string-db.org/api`, taxon 10090. Raw API responses, mapping ambiguity report, scores, provenance hashes and threshold graph metrics under `results/discovery/network/`. No fabricated edges or added neighbor genes. Candidate equations, component coverage, weights and scenario ranks under `results/discovery/candidates/`.

Plots and report consume actual measured tables. Clean source/research ZIPs contain per-file SHA-256 manifests; release CRC/exclusion/hash checks in `release/release_validation.json`. Historical exploratory Python outputs remain clearly separate from final DESeq2 inference.
