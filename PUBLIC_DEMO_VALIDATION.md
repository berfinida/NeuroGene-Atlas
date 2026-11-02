# Public Demo Validation

Status: **local review preview tested, public deployment not performed**. Date: 2026-11-02. Candidate version: 0.6.0-rc.1. Latest previously published source version: v0.5.1.

## Observed Results

| Check | Actual result |
| --- | --- |
| Scientific Python suite | 62 passed, including 23 API integration tests |
| Source/software/security suite | 28 passed |
| Full research dashboard Playwright | 30 passed; desktop/mobile Chromium |
| Review-demo Playwright | 10 passed; desktop/mobile Chromium |
| Source-only missing-data browser checks | 2 passed; desktop/mobile Chromium, no synthetic scientific results |
| Research API/download sweep | 152 successful requests covering 31 GET API route templates |
| Demo API/data-scope sweep | 40 recorded responses matched their expected success/denial status; additional read-only/host checks passed |
| Numerical comparisons | Demo scientific JSON equals existing research API values; precomputed network metrics matched rtol 1e-8 / atol 1e-10 |
| Integrity | All 59 candidate files and ZIP members verified; 204 original scientific file hashes unchanged |
| TypeScript / Next.js 15.5.28 production build | Passed |
| npm dependency audit | Zero known advisories after minimal Next.js patch |
| Python dependency audit | Zero known advisories after certifi/Pillow/pypdf repairs; initial 56 advisory entries retained separately |

The demo tests inspect 14,358 valid-FDR volcano points, genuine six-library expression, the 976-gene overlap, 48 discovery Reactome pathways and the actual 1,408-node STRING graph (4,646 associations at 0.7). Canvas-pixel checks cover all Cytoscape layers, not just its empty selection layer. Tests confirm restricted raw/archive endpoints fail closed and unsupported UI links are absent.

Local URLs used: preview frontend http://127.0.0.1:3010 / backend http://127.0.0.1:8010; research regression frontend 3008 / backend 8008. These are not public URLs. The frontend was served from the real standalone production output, not a static imitation.

## Evidence And Failures

Authoritative local records: `results/validation/phase6_20261102/tests.json`, `commands.json`, `live_api.json`, `public_demo_api.json`; separate demo reporter: `frontend/test-results-demo/results.json`. Old and new scientific artifacts remain separate from these software logs.

Initial regression browser failures came from concurrent suites deleting their shared trace directory. Demo reporter/artifact directories are now separate. Initial demo assertions also used an ambiguous 976 text locator, a disabled-option matcher that did not reflect its actual DOM property, and only the blank top canvas layer. These were corrected without changing scientific results or removing the pixel check. An intermediate test syntax error was repaired before the final successful run. Historical failed records are not evidence of a passing run.

The interrupted October runner had also attempted full validation without a build ledger. It now fails early with an actionable message; a matching build record is required. Newly executed checks are recorded separately rather than borrowing old build success.

## Not Verified

No external deployment, paid resource, data upload, DNS change, new GitHub Release, Phase 6 hosted CI, Docker execution, target-host load test, independent R refit, human validation or clinical biomarker validation is claimed. No public demo URL is invented. Data publication and licensing remain pending approval. Public GSE284723-dependent findings remain explicitly exploratory because the 10/9/8 discrepancy is unresolved.
