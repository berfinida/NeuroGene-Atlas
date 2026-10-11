# Final Test Results

Generated 2026-10-11T18:09:01.302750+00:00; overall source-tree Phase 5 status: **passed**. Exact outcome/time/command records: `results/validation/phase5/tests.json`, `commands.json`, `live_api.json`, `playwright_results.json`. Historical counts are not current outcomes.

| Check | Status | Exit | Evidence |
| --- | --- | --- | --- |
| python | passed | 0 | results/validation/phase5/python.log |
| python_dependencies | passed | 0 | results/validation/phase5/pip_check.log |
| typescript | passed | 0 | results/validation/phase5/typecheck.log |
| dependency_audit | passed | 0 | results/validation/phase5/dependency_audit.log |
| live_api | passed | 0 | results/validation/phase5/live_api.json |
| playwright | passed | 0 | results/validation/phase5/playwright.log |
| production_build | passed | 0 | results/validation/phase5/production_build.log |

Python test count: 62; API integration subset: 23. Browser stats: `{"startTime": "2026-10-11T18:08:04.945Z", "duration": 21225.838, "expected": 30, "skipped": 0, "unexpected": 0, "flaky": 0}`. Source-tree production build, TypeScript, pip dependency check and runtime npm audit are distinct executed checks. Live HTTP coverage: 151 requests / 30 registered API route templates.

Three-study R rerun status: **passed**, 24 matching CSV tables, maximum numerical difference zero, rtol 1e-8/atol 1e-10. Versions and six prepared input tables also verified. Original 204 scientific file hashes unchanged. Original calls, current temporary paths and per-stage logs in `reproduction.json`. Same R environment/host, not second-environment replication. Context fit and FASTQ alignment were not newly rerun.

## Observed Failures and Retests

First complete Phase 5 run: Python 58 passed; browser 28 passed/2 failed because the test alert locator also matched Next's route announcer. Live API runner failed on missing root import path. Both tools repaired, then rerun. Later records replace the current summary while history retains exact failures; no scientific table modified to satisfy a test. Any subsequent failures are retained similarly.

## Archive and Clean Extraction

Do not infer clean-extraction passes from these source tests. Final machine outcomes are `release/final_release_validation.json` and `release/final_extracted_validation.json`; external SHA file is `release/RELEASE_MANIFEST_SHA256.txt`. The extracted test logs and exact dependency/build/server/test commands are retained under `release/final_extracted_logs/`. When these do not exist yet, release verification is pending. The FINAL archives contain the source-test records and critical data; post-sealing extraction evidence is provided separately so the checked ZIP bytes do not change after verification.

Docker: executable lookup exit 1; not tested. Browser coverage Chromium desktop/mobile emulation, no flaky/skipped tests claimed unless current machine stats support that. Accessibility coverage is basic keyboard/names/focus/overflow checks, not complete conformance.

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
