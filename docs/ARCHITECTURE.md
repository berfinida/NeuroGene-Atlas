# Architecture

NeuroGene Atlas is organized as a reproducible analysis-first monorepo.

## Scientific Layout

- `config/`: dataset configuration and analysis thresholds
- `data/raw/`: cached immutable source files from public repositories
- `data/processed/`: validated analysis-ready matrices and metadata
- `results/*/deseq2/`: final inference, separate shrinkage, figures, sessions and provenance
- `results/discovery/`: independent comparison/sensitivity, STRING and candidate evidence
- `results/validation/`, `results/reports/`: observed tests/reproduction and scientific HTML/PDF
- `scripts/rna_seq/`: executable analysis scripts
- `docs/`: scientific provenance, methods, validation, and limitations
- `tests/`: automated checks for generated analysis artifacts

## Application and Release

Existing modules:

- `frontend/`: Next.js/TypeScript/React, Recharts, Cytoscape, responsive CSS and desktop/mobile Playwright tests
- `backend/`: FastAPI file-backed data API, structured validated parameters, graph metrics cache
- `scripts/discovery/`: completed external DESeq2, cross-model evaluation, candidate sensitivity, plots/report
- `scripts/validate_project.py`: actual exit codes, logs, command ledger and browser evidence
- `scripts/package_release.py`: separate clean source/research ZIPs with verified hashes/CRC/exclusions
- `environment.yml`, explicit ARM64 lock and Dockerfile.analysis: tested Conda runtime and untested container recipe

No database, authentication, queue or background-job service is implemented or claimed. Analysis is offline; API reads scientific tables. Next.js proxies `/api` to the configured backend (resolved at production build).

Analysis outputs should remain file-backed and manifest-traceable so the web application never needs fabricated API responses.
