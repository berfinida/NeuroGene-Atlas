# Final Technical Audit

Generated 2026-10-11T18:09:01.302750+00:00. Source inspected before edits; existing Next.js/FastAPI/Cytoscape architecture and all scientific outputs preserved. Current observed validation status: **passed**. `results/validation/phase5/tests.json` is authoritative; Phase 3/4 records remain historical, not relabelled as new passes.

## Implemented Versus Documented Inventory

| Module | Evidence path | Implemented | Limits / not implemented |
| --- | --- | --- | --- |
| Research overview / Dataset | frontend/app/page.tsx | Summary, original GEO registry, real PCA; three-study Dataset/QC selector | DE/gene expression/pathway tools remain discovery-specific |
| Quality control | frontend/app/StudyInspector.tsx | Per-study PCA, prepared/fitted totals, size factors, external Cook summaries, distance exports | Primary additionally has heatmap/distance figures; no raw-read QC |
| Differential expression | backend/main.py /api/genes | FDR/LFC/direction/estimate/search/sort/pagination/CSV | Volcano/MA are static unshrunken figures, not an interactive estimate-switching chart |
| Gene expression | frontend/app/page.tsx | Interactive per-sample raw/normalized/VST bars and gene search | Discovery only; no cross-study normalized-count comparison |
| Cross-Dataset Validation | frontend/app/DiscoveryViews.tsx | Two-study filtering/outliers/discordance/pagination/pathways | Three-study evidence is in Study Evidence/Sensitivity, not a pooled comparison |
| Functional enrichment | backend/main.py /api/pathways | Reactome search/FDR/direction/IDs/gene links/CSV | No ranked GSEA or other ontology implementation |
| STRING Network Explorer | frontend/app/NetworkView.tsx | Actual Cytoscape canvas, search, confidence, node/edge inspectors, communities, full exports | DEG-induced graph; display<=200; indirect associations, no causality |
| Candidate prioritization | scripts/discovery/prioritize_candidates.py | Six bounded components, five presets, eight rank scenarios, fixed missing denominator | Heuristic, frozen original rank; third evidence not retrospectively added |
| Study Evidence | frontend/app/ResearchViews.tsx | Search/stability/pagination, four-gene per-study effects/FDR/SE comparison | Within-study Wald intervals, not pooled/selection-adjusted |
| Statistical sensitivity | results/phase4/statistical_sensitivity.csv | 108 real perturbation rows, pair/FDR controls, plots/exports | Not exhaustive combinations or confidence intervals |
| Publication / provenance | results/publication/figure_manifest.json | 14 vector/source sets, captions/parameters/SHA, fit/reproduction indicators | Historical Phase 4 and new Phase 5 statuses distinguished |
| Scientific Reports / exports | backend/main.py | Primary ZIP, HTML/PDF, source tables, vectors, final audit files | No editable report builder or scheduled analysis service |

No database, authentication, public deployment hardening, task queue, automated FASTQ workflow, human cohort, trained biomarker model or complete accessibility certification is implemented. R environment recipe exists but container execution is unverified; Docker lookup exit 1. Manuscript/figures are research artifacts, not peer-reviewed validation.

## Defects and Repairs

- Dataset and QC views originally exposed only discovery despite three stored cohorts. Added strict three-study API selector and file-backed explorer; primary behavior preserved. Prepared and fitted library totals are separately labelled, avoiding a preprocessing-depth ambiguity.
- Fifth sensitivity scenario had no configured bar color; all five now have explicit colors.
- Missing allowed figure could cause a FileResponse runtime exception; explicit existence guard now returns HTTP 404 and a regression test covers it.
- Gene-search accepted a missing/empty query despite declared length constraint; now required and empty/missing return HTTP 422.
- Added a keyboard skip link and visible focus indicators. Basic label/keyboard/viewport tests pass where recorded; not full WCAG certification.
- Initial Phase 5 API audit runner could not import backend when executed as a script. Added root to import path. Error-state browser test matched both application alert and Next route announcer; scoped to the application error. Initial failed outcomes remain in `results/validation/phase5/history/`, not erased.

## Actual Checks

| Check | Status | Exit | Evidence |
| --- | --- | --- | --- |
| python | passed | 0 | results/validation/phase5/python.log |
| python_dependencies | passed | 0 | results/validation/phase5/pip_check.log |
| typescript | passed | 0 | results/validation/phase5/typecheck.log |
| dependency_audit | passed | 0 | results/validation/phase5/dependency_audit.log |
| live_api | passed | 0 | results/validation/phase5/live_api.json |
| playwright | passed | 0 | results/validation/phase5/playwright.log |
| production_build | passed | 0 | results/validation/phase5/production_build.log |

Scientific tests reconstruct integer inputs, sample alignment, BH, separate shrinkage, full selection universes/correlations, overlap tails, Reactome background/families, STRING scores/mappings/metrics, score components, tie order and stability. Live HTTP requests cover every registered API route template and download choice, independently of in-process TestClient tests. Playwright covers all twelve views, desktop/mobile, network canvas pixels, interaction/search/filter/pagination/downloads, switching, loading/error/retry, keyboard names, console errors and viewport overflow. A deliberate test-only simulated 503 is explicitly scoped; real scientific responses are never mocked for result assertions.

## Release, Cleanup and Operating Constraints

Source includes dependency manifests/locks, not installed `node_modules`/`.venv`. Research includes originals, real tables/figures, reports/manuscript, provenance and validation evidence. `.git`, `.next`, caches/temp/secrets and all old `release/` archives are excluded. Existing report ZIP and publication-figure ZIP are deliberately retained because download endpoints require them; these are not duplicated final releases. Old Phase 3/4 scientific artifacts remain on disk and labelled historical.

Final CRC/SHA checks and clean paired extraction are performed by `scripts/final_release.py`. Full clean verification installs dependencies afresh, starts actual extracted API/frontend and reruns Python/typecheck/build/browser tests. Until its machine record exists, extraction is unverified; details are separate from application passes to avoid circularly claiming archive tests from source-tree tests. R reproduction does not run again during extraction.

Exact executable paths and command ledgers are retained in private local audit records, not in the public source. The commands below are portable equivalents, not a claim that the deleted `.venv` was used in this audit. Python used a fresh temporary environment; Node v22.23.1.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python scripts/final_reproduction.py --rscript Rscript
.venv/bin/python scripts/final_validate.py --build-only --api-url http://127.0.0.1:8005
.venv/bin/python scripts/final_validate.py --base-url http://127.0.0.1:3005 --api-url http://127.0.0.1:8005
.venv/bin/python scripts/final_documents.py
NEUROGENE_REPORT_STEM=NeuroGene_Atlas_Scientific_Report_FINAL node frontend/scripts/report-pdf.mjs
.venv/bin/python scripts/final_release.py package
.venv/bin/python scripts/final_release.py verify
```

## Remaining Risk

Chromium emulation only, no Safari/Firefox/assistive-technology certification. Recharts 2.15.4 is deprecated upstream; npm audit has no known reported runtime vulnerabilities when current record passes, not proof of absence. Framework pinned versions are preserved to avoid an unrelated migration. API is local, read-only and lacks auth/rate limiting; public deployment needs a separate security review. Release checks cover bundled data, not future internet availability or all OS/Python combinations.
