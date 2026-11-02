# Production Security Audit

Scope: local source and production-mode services for v0.6.0-rc.1, 2026-11-02. This is not a penetration-test certificate or a claim that deployment is complete.

## Implemented Controls

- Distinct local research, review-preview and hash-approved public serving modes. Production configuration rejects unrestricted research mode.
- Explicit host allowlist and optional exact HTTPS CORS origins; wildcard hosts and credential-bearing origins are rejected. The same-origin Next.js proxy needs no browser cross-origin grant.
- Read-only requests, no user uploads, no shell/R execution endpoints and no per-request RNA-seq fits. Public network calculations use frozen metric tables at three reviewed thresholds.
- Manifest checksums, exact file inventory, symlink/path traversal rejection, safe file allowlist and bounded downloads. Raw/bulk/session/report routes are denied in demo mode.
- URI/query budgets, a bounded per-process rate limiter, four admitted requests, request-header timeout handling, generic external error messages and structured request logs without raw queries or credentials.
- Runtime-configured, read-only Next.js API proxy with fixed upstream origin, rejected path traversal/credentials/redirects and safe backend-unavailability responses. Loopback upstreams require a local-testing opt-in in production builds.
- Basic anti-sniffing, framing and referrer headers. Proposed HTTPS edge adds HSTS. API/web containers are configured non-root, read-only, with dropped capabilities and no-new-privileges.

## Issues Found And Addressed

An unlisted symlink directory could bypass the earlier directory inventory check; verification now rejects every symlink, including unused directory links. Additional tests cover this and unsafe CORS/host settings. Demo UI previously offered absent/unreviewed artifacts; only supported study PCA/distance links remain, raw expression is disabled, and restricted pages do not offer full archives.

The November npm scan flagged Next.js 15.5.27 for critical/high advisories. The working candidate uses the minimal patch 15.5.28. The prior Sharp 0.35.5 override mitigated the cited image-library condition, but did not justify ignoring framework advisories. See [the official release](https://github.com/vercel/next.js/releases/tag/v15.5.28) and [advisory](https://github.com/advisories/GHSA-2464-fhr4-w9xw). The published v0.5.1 asset was not altered.

The current Python advisory scan also identified 56 advisories across the old certifi, Pillow and pypdf pins. The candidate uses certifi 2026.10.23, Pillow 13.0.0 and pypdf 6.21.4. Before/after inventories are retained privately. These certificate/document-processing updates do not alter the pinned numerical or R analysis packages. Official fixes: [certifi](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2), [Pillow](https://github.com/python-pillow/Pillow/releases/tag/13.0.0), [pypdf](https://github.com/py-pdf/pypdf/releases/tag/6.21.4).

Current local test evidence: 28 source/software/security tests, 62 scientific tests, TypeScript/build and dependency audits. Machine ledgers are under `results/validation/phase6_20261102/`; current scan outputs, not historical zero-advisory statements, determine release readiness.

## Remaining Limits And Release Blockers

- Docker/Podman are absent, so container build, filesystem permissions, image/OS vulnerability scans, Linux resource peaks and live TLS have not been tested here. Registry digest pins are reproducibility controls, not an image-security guarantee.
- No external host, DNS, public URL, WAF, TLS deployment or public penetration test has been exercised. A full strict-nonce CSP has not been implemented. Do not describe the application as fully hardened or clinically deployable.
- Rate/concurrency limits are per process and header-timeout handling does not forcibly terminate an already-running synchronous Python thread or guarantee a maximum streaming-transfer duration. Keep one API worker initially, a protected read-only filesystem and upstream traffic controls. Next.js proxy traffic shares the backend budget; distributed/IP-aware controls need target-host design.
- Checksums are verified at startup and assume immutable mounted files afterward. Do not grant the serving user write permission to reviewed artifacts. An environment approval hash is an operator attestation, not legal clearance or a signed owner identity.
- Secret/path regex scans cannot prove absence of all sensitive content. Review archive contents, JSON, figure/PDF metadata and third-party licenses manually before approval.
- Chromium desktop/mobile emulation is not Safari/Firefox, real-device or full WCAG certification. Dependency deprecation notices are retained; they are not fabricated test failures or ignored runtime exceptions.

Approval of data exposure, hosting budget, DNS and live deployment remains a prerequisite. Public v0.6.0 publication is blocked until container/target-host security and real HTTPS browser verification pass.
