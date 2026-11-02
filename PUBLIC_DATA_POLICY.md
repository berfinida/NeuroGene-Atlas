# Public Data Exposure Policy

Status: review only, 2026-11-02. Neither the full research archive nor the new minimal candidate has been approved for public data publication.

## Complete Archive Review

The historical research archive SHA-256 remains `f211ba30301105074bde3d59596ca1645edadd1b1e993ab8f14f088f7751c3bd`. All 335 ZIP entries, including the archive manifest, were hashed and classified. The machine-readable inventory is local and Git-ignored: `results/deployment/rc1/data_exposure_inventory.json`.

| Category | Entries | Treatment |
| --- | --- | --- |
| 1: authored summaries/methods | 11 | Proposed public summary scope; still subject to owner approval |
| 2: derived research outputs | 149 | Potentially redistributable after owner license/attribution decisions |
| 3: rights/provenance review | 51 | Raw/processed inputs, STRING-related material, sessions and archives require review |
| 4: private serving exclusions | 124 | Runtime evidence, serialized fits, logs or machine-specific metadata must not be exposed verbatim |

Classification is a conservative automated triage, **not** legal clearance. It can overclassify material or miss personal metadata that does not match a pattern. Manual content/provider review is still required. Public GEO access does not grant blanket redistribution rights. MIT on original source does not relicense external data.

## Minimal Local Candidate

The revised review candidate contains 59 payload files plus `PUBLIC_MANIFEST.json`, compressed to 12,000,203 bytes. Source tables/figures are copied without numerical edits. JSON is reserialized and machine-path values withheld; original private provenance remains intact. Three study overviews are snapshots of existing verified API values, not replacement statistical analyses. Six original PCA/distance tables support honest scoped downloads. Raw counts, RDS fits, full logs, full report ZIPs/PDFs and the publication collection are not included.

The manifest records per-file SHA-256, original source hashes, transformations, source archive hash and the 204 original scientific input/output hashes supporting snapshot provenance. No R fitting or statistical recalculation is performed by the serving application.

Manifest SHA-256: `f38702de44e73c1cf5502c17be7b5c9c5123f546f942b06da2f1abd69fb557a7`.

Review ZIP SHA-256: `22791bc334b35c9c896ac06440fdb55989bbdbeb59e7ea7ec85dbbc5b8f25ec6`.

## Provider And Scientific Conditions

- Credit GEO accessions and original investigators; review dataset-specific contributor terms before approving derived expression/statistical exports.
- STRING v12 mouse associations require attribution and review of incorporated provider terms. Explain DEG selection, thresholds, derived metrics and the difference between association and causality.
- Reactome v95 mapping/enrichment uses its database-data terms; illustrations and software have different terms. No original article figure artwork is copied into the candidate.
- GSE284723 remains GEO 10 / deposited 9 / article 8. All deposited libraries were retained; no unknown exclusion reason is invented. Third-dependent findings remain exploratory and outside validated headline evidence.
- Candidates are exploratory evidence rankings, not probabilities of clinical utility, validated human biomarkers or treatment recommendations.

See [the existing license review](docs/DEPENDENCY_AND_DATA_LICENSES.md) for provider sources and [the cohort audit](docs/GSE284723_SAMPLE_AUDIT.md) for the unresolved design discrepancy.

## Enforcement

Preview is loopback-only in the supplied configuration and visibly labeled as not approved for publication. Public startup requires an operator-supplied approval hash matching the exact reviewed manifest. Every payload must match its hash; extra files and all symlinks are rejected. Bulk/raw/session/report endpoints remain denied even when corresponding local research features exist. Only fixed, bounded routes and allowlisted files are served. A changed candidate requires a new review and approval, not reuse of the previous hash.
