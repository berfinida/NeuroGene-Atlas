# Validation

## GitHub Preparation 0.5.1

Current publication-preparation evidence is separate under `results/validation/github/`; prior Phase 5 ledgers remain historical and unchanged. See `GITHUB_RELEASE_READINESS.md` for newly executed outcomes, source-only tests, security scan and artifact checks. Hosted Actions is configured, not yet run. Third-study reproduction does not resolve its 10/9/8 cohort discrepancy.

## Phase 5 Evidence

Current machine outcomes are `results/validation/phase5/tests.json`, `live_api.json`, `commands.json`, `reproduction.json`; previous Phase 4/3 counts below are historical. Three datasets' original inputs and R fits were reconstructed/rerun in isolation: 24 CSV tables matched, maximum numerical difference zero, unchanged hashes for 204 original scientific files. Existing R installation, freshly installed Python environment; not second-R-environment validation. External no-replacement and third count-filter fits were newly rerun, unlike the historical limitations below. Context-adjusted model/FASTQ alignment not rerun. Final release CRC/SHA and fresh dependency-install/extracted-app checks are separately recorded in `release/final_release_validation.json`, `release/final_extracted_validation.json`. Full current audit is `FINAL_TEST_RESULTS.md`.

## Current Phase 4 Outcomes

Observed local results: **47 Python/statistical tests passed, 0 failed**, including **15 API integration tests**. **24 Chromium E2E checks passed, 0 failed, 0 skipped, 0 flaky** across all twelve dashboard views at 1440x1000 and 390x844. Next.js 15.5.27 production build and TypeScript passed (exit 0); runtime npm audit zero advisories. Current authoritative record: `results/validation/final_validation.json`, with `phase: 4`. Prior Phase 3 records are archived under `results/validation/phase3/`; old pass counts are historical.

New integrity checks reconstruct third raw workbook/IDs/sample order, all filters/BH/shrinkage, metadata/fasting context, pair-specific universes/log overlap probabilities, all-gene selection effects, fixed universes, separate Reactome families/backgrounds, preserved candidate ranks and every component equation, cached STRING mapping/channel scores and degree/PageRank/betweenness/Louvain at 0.4/0.7/0.9. Vector SVGs are checked for absence of raster image layers; every figure/source hash and all figure-ZIP contents are verified. Current HTML embeds fourteen real figures; PDF/manuscript/audit structure and numerical facts are tested.

Historical Phase 4 failures retained: initial vector test caught raster heatmap/colorbar; initial full browser run 22 pass/2 fail from an ambiguous locator; later ZIP test caught omitted PNG previews referenced by the figure manifest. Corrected vector rendering, scoped locator, mobile scientific-notation wrapping and complete archive contents. No scientific results changed to satisfy tests. Failure records/commands under `phase4_initial_failure/`, `phase4_failures/`, `phase4_analysis_commands.md` and `executed_commands.json`.

Observed scientific runs: third default/filter fits, external measured-fasting context fit and stored-object reverse-contrast/BH/PCA audit. The original discovery isolated rerun is a preserved Phase 3 reproduction, not a newly claimed Phase 4 rerun. No independent external second-environment reproduction, FASTQ realignment, human validation or Docker execution. Docker lookup exit 1: executable unavailable. Clean paired release extraction reuses the pinned Python environment; it is not a fresh dependency installation. Release-specific verification lives in `release/release_validation.json` and `release/extracted_release_validation.json`.

Exact commands: scientific ledger `results/validation/phase4_analysis_commands.md`, machine validation ledger `results/validation/executed_commands.json`, current command logs. Figure and report generation must finish before validating archives.

## Executed Locally

```bash
python3 scripts/rna_seq/phase_a_gse156496.py
python3 -m unittest tests/test_phase_a_outputs.py
```

Historical Phase A results:

- Phase A pipeline completed successfully.
- Unit tests: 2 passed.
- Count matrix contains six non-negative integer sample columns.
- GEO sample mapping matches the configured sample design.
- No validation issues were reported by `qc_summary.json`.

## Final DESeq2 and Phase 3

```bash
Rscript scripts/rna_seq/deseq2_gse156496.R
```

DESeq2 executed successfully with R 4.4.3, DESeq2 1.46.0 and apeglm 1.28.0. Independent raw-input discovery rerun matched eight numeric tables exactly (rtol 1e-8, atol 1e-10); original hashes and versions verified. Completed log/comparison in `results/validation/`. PDF timestamps and R serialization need not match bytewise.

External default and no-replacement fits both completed; original hashes, counts, selection, unique IDs, filtering, BH, Reactome backgrounds and comparison statistics tested. An isolated second full external rerun was not performed and is not claimed.

Final observed validation: **29 Python tests passed, 0 failed**, including nine API integration tests and reconstruction of all 15 external count columns from original gzipped files. **18 Playwright tests passed, 0 failed, 0 skipped, 0 flaky** across desktop/mobile. Production Next.js 15.5.27 build and TypeScript checks passed (exit code 0). Runtime npm dependency audit: zero advisories. The initial browser run (14 passed, 4 failed from two assertion mistakes) remains preserved separately; scientific outputs were not altered to satisfy tests.

Authoritative evidence: `results/validation/final_validation.json`, `python_tests.log`, `production_build.log`, `typecheck.log`, `playwright.log`, `playwright_results.json`, `dependency_audit.json`. Exact commands recorded in `executed_commands.json` and `phase3_analysis_commands.md`.

Offline Reactome regeneration from the SHA-256-verified bundled mouse mapping reproduced the existing enrichment CSV byte-for-byte. Current discovery provenance hashes were refreshed and every listed file hash tested. Report PDF is parsed for pages and required sections; HTML images are embedded, so the report is standalone. Release verification parses every PDF page and verifies every ZIP file against its embedded SHA-256 manifest, CRC checks and forbidden-path exclusions. The legacy analysis ZIP is deliberately included in the research bundle because the existing dashboard download endpoint needs it.

Playwright covers nine dashboard views at desktop 1440x1000 and mobile 390x844: scientific data, filters/search/pagination, images, expression, report/download HTTP responses, network canvas pixels/confidence/search/evidence and candidate scoring/sensitivity. Global checks assert no runtime exceptions or viewport overflow. Release ZIP CRC/hash/exclusions verified in `release/release_validation.json`; report embeds real figures and Chromium generates PDF after decoding images.

Coverage limits: Chromium emulation only, no full assistive-technology audit/public hardening; Docker untested. Statistical sensitivity is exploratory robustness, not clinical validation.

`scripts/verify_release.py` verifies both distinct embedded manifests, safely extracts the paired ZIPs and reruns scientific/API tests against the extracted files. Results: `release/extracted_release_validation.json` and `extracted_release_tests.log`. It reuses the pinned Python environment and does not claim a fresh dependency installation.
