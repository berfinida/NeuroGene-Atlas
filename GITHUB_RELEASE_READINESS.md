# GitHub Source Release Validation

Version 0.5.1. Owner approval explicitly permits public MIT source publication to `berfinida/NeuroGene-Atlas`. Research data publication is not approved. No DOI is claimed.

## Scientific Scope

GSE284723 remains unresolved: GEO describes ten samples, deposited counts contain nine (five floxed controls/four conditional mKO), and the article figure describes eight. No sample was deleted or refitted to reconcile this. Third-dependent findings are exploratory, not validated headline evidence. See [sample audit](docs/GSE284723_SAMPLE_AUDIT.md).

All 204 original scientific files match recorded SHA-256 values. Prior same-host, same-R-environment reproduction matched 24 CSV tables, maximum numeric difference zero, rtol 1e-8/atol 1e-10. No redundant R rerun, independent analyst, clinical validation or second R installation is claimed.

## Observed Local Checks

| Check | Actual outcome |
| --- | --- |
| Scientific Python suite | 62 passed, including 23 API integration tests |
| Source-only software/API/archive suite | 14 passed; synthetic software fixtures, not invented scientific results |
| Real-data Playwright | 30 passed, zero failed/skipped/flaky; desktop/mobile, all 12 views |
| Source-only Playwright | 2 passed; honest missing-data behavior |
| API/download checks | 151 successful requests across 30 GET route templates |
| TypeScript / production build | Both exit 0 |
| Dependency consistency | pip check passed |
| Vulnerability audits | Zero known Python/npm advisories after dependency repair |
| Original scientific checksums | 204 matched, zero changed |
| Clean source extraction | Fresh dependency installation, core tests, real-data import and full validation passed |

Private machine ledgers retain exact argv, timestamps, logs and executable paths. They are deliberately excluded from public source. Historical failures are retained locally: relocated Node dependencies, archive destination canonicalization, an incorrect browser error assertion and seven initial Starlette advisories. These were repaired and retested, not hidden. Recharts 2 and Starlette's httpx TestClient adapter have deprecation warnings.

## Portable Verification Commands

These are portable equivalents; the private command ledgers identify the actual executables used.

```sh
python -m unittest discover -s tests/core -v
python scripts/repository_audit.py
python scripts/final_validate.py --build-only --api-url http://127.0.0.1:8005 --out-dir results/validation/github
python scripts/final_validate.py --api-url http://127.0.0.1:8005 --base-url http://127.0.0.1:3005 --out-dir results/validation/github
python scripts/github_source_release.py
python scripts/verify_github_source.py
```

## Publication Controls

Only clean source is staged; raw/processed data, scientific outputs, archives, installed dependencies, credentials and runtime caches are excluded. The source package has per-file SHA-256 and ZIP CRC verification; its external checksum is authoritative. Machine-specific paths are rejected by the source audit. Heuristic credential scanning includes every local Git blob, even unreachable objects; this is not a security certification.

Publish only `main` and the `v0.5.1` source Release. The Release must have exactly one uploaded asset: `NeuroGene_Atlas_Source_v0.5.1.zip`. Never upload the research ZIP. MIT covers original source/documentation, not third-party data or dependencies; see [license review](docs/DEPENDENCY_AND_DATA_LICENSES.md).

Hosted source-only CI must complete before the Release. The manual research job is intentionally skipped because no approved public research bundle exists. Local full-data validation is not hosted full-data validation. No tested Docker execution, FASTQ realignment, clinical/causal validation, penetration test or full accessibility certification is claimed.
