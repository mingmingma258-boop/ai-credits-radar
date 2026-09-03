# Architecture

## Current state

P001 now has a working catalog MVP plus a safe orchestration prototype. TASK-002 established offline catalog review, transparent eligibility triage, local credits inventory, fail-closed FREE_ONLY routing, provider contracts, and dry-run-first AI catalog review. TASK-003 adds the first safety-gated live invocation path and an Artifact-only bounded AI Worker. This does not make quota refresh, multi-provider live routing, benchmark-derived tiers, discovery, application automation, or autonomous code changes production-ready.

## Components

| Component | Responsibility | Key paths / systems | State |
|---|---|---|---|
| Catalog data | Auditable provider/program records | `data/programs.json` | Implemented |
| Catalog/validation logic | Load, validate, filter, sort, search records | `src/ai_credits_radar/catalog.py` | Implemented |
| CLI | Catalog, prototype and one-shot invoke commands | `src/ai_credits_radar/cli.py` | Implemented |
| Quality tests | Catalog, prototype, CLI, live-gate and safety regression checks | `tests/` | Implemented |
| Static web view | Lightweight catalog browsing | `web/` | Implemented (catalog only) |
| Application guidance | Human-safe application playbook | `docs/application-playbook.md` | Implemented |
| Product/prototype design | End-to-end domain model, safety and roadmap | `docs/PROTOTYPE.md` | Implemented |
| Offline Catalog Review | Deterministic catalog health report | `src/ai_credits_radar/review.py` | Prototype implemented |
| Optional AI Catalog Review | Manual dry-run/invoke Artifact workflow | `scripts/ai_catalog_review.py`, `.github/workflows/ai-catalog-review.yml` | Prototype implemented |
| Eligibility triage | Explain likely/possible/not-match from local non-sensitive profile facts | `src/ai_credits_radar/eligibility.py` | Prototype implemented; non-authoritative |
| Credits Inventory | Validate/summarize granted-resource and live attestation state | `src/ai_credits_radar/inventory.py` | Prototype implemented; local JSON |
| Free-Only Router | Select only confirmed-safe free resources, hard-stop otherwise | `src/ai_credits_radar/routing.py` | Prototype implemented |
| FREE_ONLY Gateway | Re-check route + live attestation, cap one request/output, record usage, hard-stop failures | `src/ai_credits_radar/gateway.py` | Prototype implemented; Alibaba only |
| Provider Adapter layer | Normalize credential/region/quota/model/cost/invoke/redaction contracts | `src/ai_credits_radar/providers/` | Contract + live Alibaba adapter |
| Bounded AI Worker | Read allowlisted repo context and create reviewable artifacts only | `src/ai_credits_radar/worker.py`, `scripts/free_ai_worker.py` | Prototype implemented |
| Manual Worker Action | Human-confirmed dry-run/live execution with read-only repo permissions | `.github/workflows/free-ai-worker.yml` | Prototype implemented |
| Alibaba smoke test | Manual minimal live connectivity check | `scripts/aliyun_bailian_smoke_test.py`, `.github/workflows/aliyun-smoke-test.yml` | Implemented, manual only |
| Discovery Engine | Find public candidate offers from official/public sources | planned | Planned |
| Verification Engine | Resolve candidate status, freshness, conflicts, expiry | planned | Planned |
| Application Assistant | Prepare truthful materials and human-gated application state | planned | Planned |
| Model Registry / Benchmark | Evidence-based capability classification | planned | Planned |
| Multi-provider task runner | Route real work across multiple confirmed-free providers | planned | Planned |
| Notification / orchestration dashboard | Surface new/changed/expiring/blocked/running state | planned | Planned |

## Data flow

Long-term target flow:

```text
Public/official sources
        ↓
Discovery (candidate)
        ↓
Verification + conflict/freshness checks
        ↓
Eligibility/risk assessment
        ↓
Application preparation ──→ WAITING_FOR_HUMAN for auth/verification/payment/final submit
        ↓
Approved/granted resource inventory
        ↓
FREE_ONLY Router
        ↓
Live-use attestation + Gateway preflight
        ↓
Provider Adapter
        ↓
Capability-aware bounded invocation
        ↓
AI Worker Artifact
        ↓
Strong Chat / human review
        ↓
Human-approved repository change
```

TASK-003 implements the first Alibaba-only live path from local inventory to one bounded model request and an Artifact-only worker. It deliberately does not let the model write the repository or choose paid fallback.

## Interfaces / contracts

- Catalog records remain machine-readable and validated; schema evolution must be backward-aware and tested.
- Verified offer claims require official evidence and freshness metadata.
- Eligibility triage is advisory only and must expose blockers/warnings/positives instead of claiming provider approval.
- Real profile, inventory, worker tasks and usage state belong in ignored local files or approved private storage, not committed public data.
- Credits inventory explicitly distinguishes `billing_state` and `quota_state`; unknown is unsafe.
- Live use additionally requires `allow_live`, a recent confirmation timestamp, provider id, Free Quota Only/stop protection, paid-fallback-disabled state, `max_requests_per_run=1`, and a small output-token cap.
- Committed synthetic example inventory can be used for dry-run but can never authorize a live request.
- Provider adapters do not decide that usage is free. The gateway owns FREE_ONLY authorization. Direct Alibaba adapter invocation is blocked unless gateway-authorized.
- Alibaba `403 AllocationQuota.FreeTierOnly` is an expected safe exhaustion stop; it is never a retry or paid-fallback signal.
- Worker context is explicit and bounded: max eight allowlisted repository files, restricted file types, repository-root confinement, and a total context cap.
- Worker output is Artifact-only. It cannot run shell commands, edit files, access secrets, push, open PRs, or merge.
- Human-gated application states remain explicit rather than simulated as successful automation.

## External dependencies

- Provider public documentation, pricing/free-tier/program pages, official APIs, and consoles can change.
- GitHub Actions is used for CI and selected manual jobs.
- Provider credentials remain in environment/secret storage and never in committed state.
- PR CI remains offline with respect to provider APIs. The manual worker exposes `DASHSCOPE_API_KEY` only in the explicit live step after per-run confirmations.
- Alibaba currently documents Free Quota Only / stop-when-exhausted as the provider-side mechanism that returns `AllocationQuota.FreeTierOnly` after free quota exhaustion.

## Security and privacy boundaries

- No secrets or identity/payment data in committed state or logs.
- Unknown billing or quota state is unsafe by default.
- Provider calls are one-shot and explicitly authorized; normal CLI/CI flows do not invoke providers.
- No automatic provider/model retry or paid fallback.
- Login, OAuth, CAPTCHA/verification, SMS/TOTP, identity/student verification, payment methods, potentially paid service enablement, and final submission require human takeover.
- Application assistance may improve truthful wording but may not invent eligibility facts.
- AI review/worker output cannot automatically promote catalog data or modify/merge repository changes.

## Testing strategy

- Structural workflow state: `python scripts/check_ai_state.py`
- Catalog validation: `credits-radar validate`
- Regression/unit/integration tests: `python -m unittest discover -s tests -v`
- Offline vertical smoke flow: `review`, `eligibility`, `inventory`, `route`, `invoke --dry-run`, AI-review `dry-run`, and Worker `dry-run` run in `.github/workflows/ci.yml`.
- Live network behavior is mocked in tests. No provider invoke mode is run in PR CI.
- Tests cover stale/missing protection, example-inventory live rejection, direct-adapter blocking, one-request behavior, `AllocationQuota.FreeTierOnly`, context traversal, and workflow secret scoping.

## Technical debt / known constraints

- Current catalog schema predates the full candidate → verified lifecycle and structured eligibility fields; future schema evolution should be staged rather than destructive.
- Eligibility triage uses explicit program type plus transparent text signals; it is not a provider-specific eligibility parser.
- Inventory and remaining quota are still human-maintained; P001 does not yet refresh provider quota automatically.
- Alibaba live authorization relies on a recent human console attestation plus provider-side Free Quota Only protection. API success is never treated as proof of free billing.
- Capability tiers are accepted as local inventory facts but are not yet produced by a benchmark engine.
- The Worker produces proposals/patch text only; applying changes remains a separate reviewed executor/human step.
- Discovery, application-state automation, live multi-provider routing, benchmark promotion, and orchestration dashboard remain planned.
