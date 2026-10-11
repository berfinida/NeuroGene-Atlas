# Release And Data Strategy

## Source Versus Research Artifacts

Version 0.5.1 source is Git-ready but unpublished. Ignore `data/`, `results/`, `release/`, installed dependencies, caches and ZIPs. Original local research evidence remains intact. Previous 0.5.0 FINAL ZIPs and extraction evidence are historical verified artifacts, not the new source release.

The local source ZIP contains source/configuration, locks, tests, documentation and actual screenshots only. The approximately 100 MiB raw-inclusive research ZIP must **not** enter ordinary Git history or be uploaded publicly until redistribution rights and owner approval are established. A future approved derived-only bundle should avoid duplicating raw inputs and preserve original-input URLs/checksums.

## Original Public Inputs

Primary input URLs are in `config/gse156496.json`:

- [GSE156496 integer counts](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE156nnn/GSE156496/suppl/GSE156496_RNAseq_RawCountTable.txt.gz)
- [GSE156496 original metadata](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE156nnn/GSE156496/matrix/GSE156496_series_matrix.txt.gz)
- [GSE132741 metadata](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE132nnn/GSE132741/matrix/GSE132741_series_matrix.txt.gz): `scripts/discovery/prepare_independent.py` selects 15 eligible 30-week TA libraries and fetches each deposited `fragmentspergene.counts.txt.gz` URL; excludes other tissues/genotypes/ages and ambiguous bridges. See processed provenance for exact library URLs/hashes.
- [GSE284723 counts](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE284nnn/GSE284723/suppl/GSE284723_rawCounts.xlsx) and [metadata](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE284nnn/GSE284723/matrix/GSE284723_series_matrix.txt.gz). Third-cohort findings remain restricted as documented in the sample audit.
- [Reactome v95 Ensembl mapping](https://download.reactome.org/95/Ensembl2Reactome.txt); filter mouse records, preserve source SHA and release identifier. STRING v12 mouse associations and input-to-protein mapping are cached with evidence provenance under discovery results.

These public originals do not alone reconstruct every cached derived artifact: annotation bridges, exact database snapshots and historical report/audit files are required for byte-complete reproduction. Until an approved pinned research bundle is hosted, full clean-clone research tests are opt-in using the verified local bundle. No automatic full clean-clone scientific-data bootstrap is claimed.

## Versions And Checksums

The Phase 5 historical research archive SHA-256 is `f211ba30301105074bde3d59596ca1645edadd1b1e993ab8f14f088f7751c3bd` (105,214,892 bytes). Source 0.5.0 SHA is `34fd0706407afeecbb596e7aa93a14d1d6b43657d999597a01403f75e863a136` (224,945 bytes). Verify using `shasum -a 256 -c RELEASE_MANIFEST_SHA256.txt` in `release/`.

New source artifacts and exact per-file hashes are recorded separately in `release/github/`. Package locks, analysis parameters, database versions and original-input hashes remain in the repository configuration and research provenance. Do not reuse old SHA values for repackaged bytes.

## GitHub And Zenodo

Intended account `berfinida`; name `NeuroGene-Atlas`; main branch. The authenticated read-only query found no target repository. No remote, repository, release or DOI has been created by this preparation.

After explicit owner approval, publish verified source only. Configure private vulnerability reporting and branch protection; review the first hosted CI run. A source-only draft release can use the 0.5.1 ZIP and SHA manifest. Scientific datasets need a separate rights review and approval. Consider Zenodo software archival after a versioned release exists; do not claim a DOI before deposition. Archived data require original-provider terms, appropriate attribution and an explicit license decision.

Exact conditional publication commands are in `GITHUB_RELEASE_READINESS.md`; nothing is automatically pushed or uploaded by the local packaging scripts.
