# Deployment Architecture

Status: local v0.6.0-rc.1 preparation, 2026-11-02. No hosting resource, public demo, DNS change or new Release has been created.

## Selected Design

Use a small Linux VM with Docker Compose: Caddy terminates HTTPS, Next.js serves the existing dashboard and a same-origin runtime API proxy, and a private FastAPI service serves an immutable, read-only reviewed-results mount. Only the edge publishes ports 80/443. The application does not require a database, Redis, object storage, authentication service or RNA-seq execution service.

The backend is intentionally different from an analysis worker: it reads frozen results. Demo network requests load the existing 0.4/0.7/0.9 metric tables instead of recalculating communities or centralities. R and raw count inputs are not installed in the serving image. Browser requests use relative `/api/` URLs; `API_INTERNAL_URL` is read by the Next.js server at runtime, not baked into the client build.

## Hosting And Cost Review

Prices are planning estimates, not an authorization to purchase. Recheck the provider checkout, region, stock and taxes before approval.

| Option | Expected base cost | Assessment |
| --- | --- | --- |
| DigitalOcean Basic Regular, 2 vCPU / 4 GiB / 80 GiB SSD | USD 24/month | Recommended approval candidate: enough starting headroom for both services, simple read-only local artifact mount, no separate data-hosting service |
| Render frontend 0.5c/512 MB plus backend 1c/2 GB | Approximately USD 32/month compute, plus any disk/transfer charges | Managed alternative; private artifact staging must be designed before use; the supplied Compose configuration is not a Render blueprint |
| Hetzner cost-optimized CX23 | No current purchase quote | The official page currently reports unavailable stock; do not promise its historical low price |
| Render Free | USD 0 within quotas | Preview only: idle sleep, cold start and ephemeral filesystem; not the recommended always-on scientific service |

The recommended VM includes 4,000 GiB transfer under the currently listed plan. Domain registration, optional backups, tax and overages are excluded from USD 24. No optional paid service is selected. [DigitalOcean pricing](https://www.digitalocean.com/pricing/droplets), [Render pricing](https://render.com/pricing), [Render compute specifications](https://render.com/docs/compute-plans), [Render free restrictions](https://render.com/docs/free), [Hetzner availability](https://www.hetzner.com/cloud/cost-optimized/).

## Capacity And Storage

Compose reserves limits of 1 GiB for the API, 512 MiB for the web process and 256 MiB for Caddy. These are initial engineering budgets, not measured Linux peak-memory requirements or concurrency certification. A 4 GiB host leaves OS and build headroom; build API and frontend images sequentially. Target-host load tests and OOM monitoring remain required.

The candidate has 59 payload files, 28,910,080 uncompressed payload bytes and a 12,000,203-byte ZIP. Budget at least 10 GiB for images, build cache and logs, separate from this small artifact. Never mount the approximately 100 MB full research archive, workspace root or original `data/` tree into the public service. No scientific cache needs a writable persistent database. TLS state is stored in Caddy volumes and must be protected separately.

## Approval Boundary

`compose.local.yml` exposes only loopback ports 3010/8010 and uses review-preview mode. `compose.production.yml` requires an approved manifest hash, a reviewed-results directory and an explicitly approved domain. Public mode refuses to start with a missing/mismatched approval hash, invalid files or extra/symlink content. Setting an environment variable is an operator attestation, not a legal license grant or a cryptographic owner signature.

Proposed URL format: `https://neurogene-atlas.<owner-approved-domain>`. This is a placeholder, not an existing or reserved domain. Docker execution, external TLS, hosted load/security testing and live deployment are not yet verified. No v0.6.0 Release may be published until those checks and explicit approvals are complete.
