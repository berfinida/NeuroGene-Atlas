# Dependency And Data License Review

Reviewed during local 0.5.1 preparation, 2026-10-11. This is a scoped technical review, not legal certification.

## Source And Dependencies

MIT applies only to original code/documentation. Preserve dependency notices when redistributing software. npm lock metadata was inventoried for all packages (including optional binaries); installed Python metadata and R DESCRIPTION license fields were inspected. Full inventories: `results/validation/github/npm_licenses.json`, `python_licenses.json`.

Frontend metadata includes MIT, ISC, BSD/0BSD, Apache-2.0, CC-BY-4.0 and LGPL-3.0-or-later combinations in Sharp/libvips-related optional binaries. Do not treat bundled native dependencies as uniformly MIT. Python includes BSD/MIT/Apache/PSF, MPL-2.0 (certifi), MIT-CMU (Pillow), and numerical-wheel bundled notices. Copyleft/notice obligations require a separate review if distributing containers or native runtime binaries; this source ZIP contains neither installed dependencies nor R binaries.

Installed R: DESeq2 1.46.0 `LGPL (>= 3)`; apeglm 1.28.0 `GPL-2`; jsonlite 2.0.0 `MIT + file LICENSE`. Their code is not relicensed by the project's MIT license. Environment configuration merely references separately installed packages.

## Data And Publication Material

| Provider | Observed terms and release decision |
| --- | --- |
| GEO/NCBI mouse inputs | Public download access; NCBI does not restrict molecular-data distribution but cannot transfer contributors' rights or grant unrestricted permission. Preserve accessions, authors, URLs and hashes. Raw-inclusive publication remains pending dataset-specific review. |
| Reactome v95 mapping | Database data/derived files are CC0 under current official policy; illustrations/branding CC-BY-4.0 and software usually Apache-2.0 have different scopes. Our mapping/enrichment tables are not copied branding. |
| STRING v12 mouse data | Current official terms specify CC-BY-4.0; credit STRING and disclose gene selection, score thresholds, inferred communities and derived centrality. Incorporated third-party material retains original-provider terms. |
| GSE284723 article | CC-BY-NC-ND-4.0; do not copy or adapt its figure artwork under project MIT. Dashboard figures are computed independently. |
| Figshare 30090307 | API metadata reports CC-BY-4.0 for its workbook; reviewed for sample audit only, not bundled as new primary RNA-seq evidence. |

Official policies: [NCBI](https://www.ncbi.nlm.nih.gov/home/about/policies/), [Reactome](https://reactome.org/license), [STRING](https://string-db.org/cgi/access), [article copyright notice](https://pmc.ncbi.nlm.nih.gov/articles/PMC12673120/), [Figshare metadata](https://api.figshare.com/v2/articles/30090307).

## Vulnerabilities And Permission Boundary

Initial pinned Python scan found seven advisories in Starlette 0.46.2, including FileResponse Range-header denial of service ([official advisory](https://github.com/Kludex/starlette/security/advisories/GHSA-7f5h-v6xp-fcq8)). Updated FastAPI 0.143.0 / Starlette 1.3.1 and pinned transitive additions. The subsequent pip-audit run found no known vulnerabilities; preserve before/after JSON. npm audit (including development dependencies) also reported zero. Database coverage is not proof of complete security.

Servers bind localhost. No credential values were printed or copied into release artifacts. No public repository, release, remote push, data upload or DOI deposition occurred. Repository owner must approve source licensing/publication, configure a private reporting contact and separately approve any data redistribution.
