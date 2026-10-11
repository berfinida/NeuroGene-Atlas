# NeuroGene Atlas

## Final Release / Phase 5

Current audit and source-test evidence: `FINAL_SCIENTIFIC_AUDIT.md`, `FINAL_TECHNICAL_AUDIT.md`, `PUBLICATION_READINESS.md`, `DATASET_COMPARISON_SUMMARY.md`, `CANDIDATE_GENE_EVIDENCE.md`, `FINAL_TEST_RESULTS.md`, `results/validation/phase5/`. Historical Phase 3/4 records below remain labelled historical; do not infer current pass counts from them.

Three original count inputs were reconstructed and all R scripts rerun in an isolated temporary root. Twenty-four stored CSV tables matched with maximum numerical difference zero (rtol 1e-8, atol 1e-10). Same host and pinned R installation, not a second R environment or independent biological validation. Dataset/QC now switch among all three actual studies; discovery DE, expression and enrichment tools keep their original discovery-specific scope.

Final deliverables: `release/NeuroGene_Atlas_Source_FINAL.zip`, `release/NeuroGene_Atlas_Research_Results_FINAL.zip`, `release/RELEASE_MANIFEST_SHA256.txt`. Extract both ZIPs into one root, then use Quick Start below. Dependency manifests and locks are included; installed packages are excluded. New standalone report: `results/reports/NeuroGene_Atlas_Scientific_Report_FINAL.html` and `.pdf`. Original scientific outputs and historical reports are preserved.

Final verification:

```bash
.venv/bin/python scripts/final_reproduction.py --rscript Rscript
.venv/bin/python scripts/final_validate.py --build-only --api-url http://127.0.0.1:8000
# Start both servers with the Quick Start commands, then:
.venv/bin/python scripts/final_validate.py --base-url http://127.0.0.1:3000 --api-url http://127.0.0.1:8000
.venv/bin/python scripts/final_documents.py
NEUROGENE_REPORT_STEM=NeuroGene_Atlas_Scientific_Report_FINAL node frontend/scripts/report-pdf.mjs
.venv/bin/python scripts/final_release.py package
.venv/bin/python scripts/final_release.py verify
```

Clean verification installs fresh Python/Node dependencies in a temporary extracted root, starts its API/frontend and runs Python, TypeScript, production build and Chromium desktop/mobile tests. Final extraction logs/commands are published separately in `release/final_extracted_validation.json` and `release/final_extracted_logs/`, after sealing ZIP bytes. No Docker run or full WCAG/public-security certification is claimed.

Scientific transcriptomics dashboard for verified mouse RNA-seq analyses. Phase 4 preserves discovery and Phase 3 outputs, audits selection bias, adds a separately fit conditional mouse cohort and exposes study-specific candidate evidence. No clinical biomarker claims.

Discovery dataset `GSE156496`:
mouse tibialis anterior muscle, three WT controls and three Dmd exon 51 knockout samples.

## Current Status

- Official GEO raw count table is cached under `data/raw/GSE156496/`.
- Sample metadata are parsed from the official GEO series matrix.
- Python validation and QC outputs are executable locally.
- Actual DESeq2 and apeglm completed: 14,359 tested genes; 1,499 DEGs (1,323 up / 176 down).
- Isolated raw-input reproduction matched eight numeric tables exactly (rtol 1e-8, atol 1e-10).
- GSE132741 independent mouse TA: 7 WT / 8 mdx, GEO-labelled 30 weeks; 2,419 default DEGs, 2,019 without outlier replacement. Not clinical validation.
- Across 12,814 shared inference genes: 976 overlapping DEGs, 973 concordant / 3 discordant, Pearson r=0.765540, Spearman rho=0.685506. 30 shared significant Reactome all-DEG pathways.
- STRING 12.0: 1,408 mapped genes, 17,872 associations >=0.4; interactive Cytoscape explorer.
- 1,499 preserved exploratory rankings; eight rank sensitivity scenarios. Third-study evidence remains separate from heuristic scores.
- GSE284723: nine deposited libraries (5 floxed controls / 4 conditional mKO), 15,009 tested genes, 1,817 DEGs; 870 discovery-overlapping DEGs (868 concordant / 2 discordant).
- 572 candidates concordant across three studies and count-filter/outlier alternatives; 555 also pass measured fasting adjustment. These are conditional, exploratory findings.
- 108 pairwise threshold/context/filter/outlier settings, study-specific and common-background Reactome tables, 14 vector figures with captions/parameters/source CSVs.
- Original discovery age corrected to one month. All-common-effect discovery/mdx sign agreement 75.3%, versus 99.7% in selected overlapping DEGs: selection matters.
- Formal audit: `SCIENTIFIC_AUDIT_REPORT.md`; manuscript: `SCIENTIFIC_MANUSCRIPT_DRAFT.md`. Third deposited-versus-published sample counts, sex and biological independence limitations remain explicit.

## Quick Start

Extract source and research ZIPs into the same project root. Python 3.14 / Node 22 tested. Run in separate terminals:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm ci
API_INTERNAL_URL=http://127.0.0.1:8000 npm run build
npm run start -- --port 3000
```

Open http://127.0.0.1:3000. API proxy URL is resolved during build. All twelve scientific views use actual stored results. Do not rebuild `.next` while testing the running production server.

## Historical Preparation

```bash
python3 scripts/rna_seq/phase_a_gse156496.py
```

Historical Python statistics are exploratory and never final DESeq2 inference. Archived Phase 3 validation/report artifacts retain their original claims; consult current Phase 4 audit and `results/validation/final_validation.json` for current outcomes.

## Phase 4 Reproduction

Use the pinned Python environment and R environment described below. GEO review reuses cached original files and downloads only missing sources. Analyses are per-study, never pooled. Existing Phase 3 analyses need not be rerun to open the app.

```bash
.venv/bin/python -m scripts.discovery.review_geo
.venv/bin/python scripts/discovery/prepare_third.py
Rscript scripts/discovery/third_deseq2.R
.venv/bin/python -m scripts.discovery.metadata_audit
Rscript scripts/discovery/context_sensitivity.R
Rscript scripts/discovery/audit_fits.R
.venv/bin/python -m scripts.discovery.phase4_analysis
MPLCONFIGDIR=/tmp/neurogene-mpl .venv/bin/python -m scripts.discovery.publication_figures
.venv/bin/python -m scripts.discovery.phase4_documents
cd frontend
npx playwright install chromium
node scripts/report-pdf.mjs
```

The primary isolated reproduction was performed in Phase 3 and its eight matching tables are preserved. Phase 4 recalculated contrasts and BH from stored fitted objects for all three studies. External fits are not independently reproduced in a second environment. Counts were reanalyzed; FASTQ alignment was not repeated. Docker is unavailable locally and its recipe remains untested.

With backend/frontend running together, run `scripts/validate_project.py --build-only` before starting the production frontend, then `scripts/validate_project.py --base-url ... --api-url ...`. Regenerate the report after observed validation, then run `scripts/package_release.py` and `scripts/verify_release.py`. The two ZIPs must be extracted into the same root. Figure collection: `results/publication/NeuroGene_Atlas_Publication_Figures.zip`.

Expected outputs:

- `data/processed/GSE156496/sample_metadata.csv`
- `data/processed/GSE156496/count_matrix.csv`
- `results/GSE156496/qc_summary.json`
- `results/GSE156496/library_sizes.csv`
- `results/GSE156496/pca_samples.csv`
- `results/GSE156496/sample_distances.csv`
- `results/GSE156496/exploratory_de_not_deseq2.csv`
- `results/GSE156496/analysis_manifest.json`

## DESeq2

Install pinned `environment.yml` or tested macOS ARM64 explicit `environment.osx-arm64.lock.txt`, then run with `Rscript` on PATH. Docker recipe supplied but untested.

```bash
Rscript scripts/rna_seq/deseq2_gse156496.R
```

The DESeq2 script uses raw integer counts, models `~ condition`, sets `WT` as the reference group, and reports the contrast `D51_vs_WT`.

## Phase 3 Commands

```bash
.venv/bin/python -m scripts.rna_seq.reactome_enrichment
.venv/bin/python -m scripts.discovery.prepare_independent
Rscript scripts/discovery/independent_deseq2.R
.venv/bin/python -m scripts.discovery.evaluate_replication
.venv/bin/python -m scripts.discovery.prioritize_candidates
MPLCONFIGDIR=/tmp/neurogene-mpl .venv/bin/python -m scripts.discovery.research_figures
.venv/bin/python scripts/rna_seq/package_analysis.py
.venv/bin/python -m unittest discover -s tests -v
```

Browser validation, with both servers running:

```bash
cd frontend
npm run typecheck
npx playwright install chromium
E2E_BASE_URL=http://127.0.0.1:3000 npx playwright test
```

STRING retrieval is version-pinned in `scripts/discovery/string_network.py`; cached raw responses are reused offline. Report/release generation from the project root:

```bash
.venv/bin/python -m scripts.discovery.phase4_documents
node frontend/scripts/report-pdf.mjs
.venv/bin/python scripts/package_release.py
.venv/bin/python scripts/verify_release.py
```

Deliverables: `release/NeuroGene_Atlas_Source.zip`, `release/NeuroGene_Atlas_Research_Results.zip`, standalone HTML/PDF under `results/reports/`. ZIP CRC and per-file SHA-256 verified; heavy runtime dependencies excluded. Exact observed commands/tests: `results/validation/`. External fits executed and tested, but an isolated second external full rerun was not performed.

[Methods](docs/SCIENTIFIC_METHODS.md), [validation](docs/VALIDATION.md), [limitations](docs/LIMITATIONS.md), [provenance](docs/DATA_PROVENANCE.md).

## Scientific Guardrails

Current observed Phase 4 validation: 47 Python tests (including 15 API integration tests) and 24 desktop/mobile Playwright tests passed; production build and TypeScript passed; runtime dependency audit had zero advisories. Full commands/exit codes and prior failures are preserved in `results/validation/`. Discovery was independently reproduced in Phase 3; external counts and fits are tested, but no second isolated external reproduction is claimed. ZIP CRC/SHA-256 and extracted-release tests are performed by the release scripts.

The exploratory Python differential table is not a DESeq2 substitute. It is included only so QC, normalization, PCA, and table plumbing can be exercised in an environment without R. Do not cite it as final differential expression evidence.
