# Deployment Guide

This guide prepares v0.6.0-rc.1 locally. The published v0.5.1 source Release is not overwritten. No public dashboard URL exists for this candidate.

## Local Installation

Use Python 3.14 and Node 22. Install from the existing locks; no R rerun is necessary to serve verified outputs.

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
cd frontend
npm ci
npx playwright install chromium
cd ..
```

Preparing a fresh data candidate requires the private local research archive and original verified results. The script checks 204 original file hashes and the historical archive SHA, copies results and creates sanitized JSON snapshots. It refuses to overwrite a candidate directory. Choose a new output directory for a new revision; never delete original scientific evidence to make it run.

```sh
.venv/bin/python scripts/prepare_public_demo.py --output-dir results/deployment/rc1
```

This operation is **not** permission to publish that directory or ZIP. Existing review artifacts may already be present; validate and reuse them instead of regenerating them unnecessarily.

## Local Services Without Docker

Run the preview backend in one terminal:

```sh
NEUROGENE_MODE=preview NEUROGENE_ENV=production \
NEUROGENE_DATA_ROOT="$PWD/results/deployment/rc1/public_candidate" \
NEUROGENE_ALLOWED_HOSTS=127.0.0.1,localhost \
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010 --no-proxy-headers
```

Build once, copy static assets into the standalone output, then start the frontend in another terminal:

```sh
cd frontend
npm run typecheck
npm run build
cp -R .next/static .next/standalone/.next/
API_INTERNAL_URL=http://127.0.0.1:8010 NEUROGENE_ALLOW_LOCAL_API=1 \
HOSTNAME=127.0.0.1 PORT=3010 node .next/standalone/server.js
```

Local preview: http://127.0.0.1:3010. Backend liveness/readiness: http://127.0.0.1:8010/healthz and http://127.0.0.1:8010/readyz. Loopback is intentionally allowed only by an explicit local-testing flag. Root `.env.example` is documentation, not an automatically loaded configuration file.

For full regression testing, run a separate local research backend on 8008 without `NEUROGENE_ENV=production`, and the same frontend build on 3008 with runtime API destination 8008. Never expose research mode publicly. Run `final_validate.py --build-only` with the intended `--out-dir` before full validation; stop frontends before rebuilding their shared output.

## Docker Preparation

Docker/Podman were unavailable in this environment. The configurations are prepared, not claimed container-tested. On an approved local Docker installation:

```sh
docker compose -f compose.local.yml config
docker compose -f compose.local.yml build api
docker compose -f compose.local.yml build web
docker compose -f compose.local.yml up -d
```

Review health checks, verify downloads and repeat browser/security tests against these containers before external deployment. Base images are digest-pinned to previously retrieved official registry manifests; pinning does not establish that their OS packages are vulnerability-free. Re-scan images and refresh digests before release if required.

## External Deployment: Approval Required

Do not execute this section until the owner explicitly approves the provider/cost, exact 59-file inventory and manifest, data-license decisions, domain/DNS and public exposure. The initial recommended compute budget is USD 24/month before taxes/domain/optional extras; see the architecture review.

1. Use the provider dashboard to provision the approved Linux host, add the owner's SSH public key and configure a firewall. Do not share private keys, passwords or cloud API tokens in chat.
2. Transfer clean source and **only the approved candidate directory** through a secure administrative channel. Do not copy the full research archive. Stage the approved directory outside the Git checkout with read-only permissions for UID 10001.
3. In provider-managed configuration or a protected operator environment, set `APPROVED_RESULTS_DIR`, `DATA_APPROVAL_SHA256` and `PUBLIC_DOMAIN`. The manifest approval value must equal the SHA-256 of the exact `PUBLIC_MANIFEST.json`; it must not be assigned before actual owner approval. No scientific API key is required.
4. Review the expanded production Compose configuration. Build images sequentially. Open only 80/443 to the public and restrict administrative SSH access. Do not publish API or web container ports directly.
5. Start the approved Compose project; Caddy will perform TLS issuance. Verify the actual HTTPS URL in a browser, desktop/mobile scientific workflows, unavailable-data states, safe downloads, HTTP-to-HTTPS behavior, headers, request budgets and logs.
6. Run target-host/container and dependency vulnerability scans, record production smoke-test evidence and monitor memory/latency. Stop and roll back if hashes, science or access boundaries differ.
7. Only after successful live verification and separate Release approval, prepare and publish v0.6.0. Do not modify the existing v0.5.1 tag or asset.

## Rollback

Keep the previous image digests and approved manifest outside Git. Stop the new services, restore the prior approved read-only directory and image versions, and repeat readiness/scientific smoke checks. Preserve failed logs privately. Do not roll back or edit scientific tables to make a test pass. For local cleanup use `docker compose down` without deleting scientific files or TLS volumes unintentionally.
