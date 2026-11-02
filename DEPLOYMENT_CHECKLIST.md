# Deployment Checklist

## Local Preparation

- [x] Preserve v0.5.1 and original scientific results.
- [x] Separate research / review-preview / public runtime configuration.
- [x] Classify all 335 research-archive entries; prepare a smaller local review candidate.
- [x] Verify 59 candidate file hashes and all 204 original scientific hashes.
- [x] Add health/readiness endpoints, safe serving, origin/host policy and basic request budgets.
- [x] Preserve scientific functionality and add real interactive volcano plotting.
- [x] Remove unsupported demo download links and retain prominent GSE284723/clinical-scope warnings.
- [x] Build the standalone frontend; run scientific, API, security and desktop/mobile tests.
- [x] Prepare digest-pinned API/web images and local/production Compose configuration.
- [x] Keep research artifacts and runtime/test caches out of source packaging.

## Before Any External Action

- [ ] Obtain owner approval of provider, exact spend ceiling, region and ongoing operator responsibilities.
- [ ] Manually approve provider/contributor terms and the precise candidate file inventory/hash.
- [ ] Obtain explicit permission to expose these research outputs.
- [ ] Select and approve the domain/public URL and DNS changes.
- [ ] Configure any cloud credentials through provider-managed secrets; never in chat or Git.
- [ ] Build/test the containers on a supported engine and scan complete images/OS packages.
- [ ] Confirm non-root volume permissions, immutable artifacts, backup/rollback and log-retention policy.
- [ ] Re-scan dependencies immediately before deployment; do not reuse stale zero-advisory statements.

## Before v0.6.0 Release

- [ ] Verify readiness, HTTPS/TLS, downloads, scientific consistency and browser flows at the actual approved live URL.
- [ ] Measure Linux memory/latency/concurrency and verify upstream traffic limits.
- [ ] Complete target-host security review and documented residual-risk acceptance.
- [ ] Run hosted source CI for the exact release commit; optional full-data CI requires separate approved data access.
- [ ] Re-run scientific/software/browser tests and record exact outcomes.
- [ ] Obtain explicit approval for a new GitHub Release; never overwrite v0.5.1.
- [ ] Attach only the specifically approved release assets. A local review ZIP is not a public data grant.

Completion of local preparation is not completion of public production deployment.
