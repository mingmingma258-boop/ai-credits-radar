# Architecture

## Current state

P001 now has a working catalog MVP plus a safe vertical-slice orchestration prototype. The repository preserves the auditable JSON catalog, Python CLI, standard-library tests, static web view, application guidance, CI, and manually triggered Alibaba Cloud Model Studio smoke test. TASK-002 adds offline catalog review, transparent eligibility triage, a local credits inventory, a fail-closed FREE_ONLY router, a provider-adapter contract, and a manual dry-run-first AI catalog-review workflow. These prototype components do not imply that automated discovery, live multi-provider routing, benchmark-based tiers, or AI workers are production-ready.

## Components

| Component | Responsibility | Key paths / systems | State |
|---|---|---|---|
| Catalog data | Auditable provider/program records | `data/programs.json` | Implemented |
| Catalog/validation logic | Load, validate, filter, sort, search records | `src/ai_credits_radar/catalog.py` | Implemented |
| CLI | Human-facing catalog and prototype commands | `src/ai_credits_radar/cli.py` | Implemented |
| Quality tests | Catalog, prototype, CLI and safety regression checks | `tests/` | Implemented |
| Static web view | Lightweight catalog browsing | `web/` | Implemented (catalog only) |
| Application guidance | Human-safe application playbook | `docs/application-playbook.md` | Implemented |
| Product/prototype design | End-to-end domain model, safety and roadmap | `docs/PROTOTYPE.md` | Implemented |
| Offline Catalog Review | Deterministic catalog health report | `src/ai_credits_radar/review.py` | Prototype implemented |
| Optional AI Catalog Review | Manual dry-run/invoke Artifact workflow | `scripts/ai_catalog_review.py`, `.github/workflows/ai-catalog-review.yml` | Prototype implemented |
| Eligibility triage | Explain likely/possible/not-match from local non-sensitive profile facts | `src/ai_credits_radar/eligibility.py` | Prototype implemented; non-authoritative |
| Credits Inventory | Validate/summarize granted-resource state | `src/ai_credits_radar/inventory.py` | Prototype implemented; local JSON |
| Provider Adapter layer | Normalize credential/region/quota/model/cost/invoke/redaction contracts | `src/ai_credits_radar/providers/` | Contract + offline Alibaba prototype |
| Free-Only Router | Select only confirmed-safe free resources, hard-stop otherwise | `src/ai_credits_radar/routing.py` | Prototype implemented; local inventory only |
| Alibaba smoke test | Manual minimal live connectivity check | `scripts/aliyun_bailian_smoke_test.py`, `.github/workflows/aliyun-smoke-test.yml` | Implemented, manual only |
| Discovery Engine | Find public candidate offers from official/public sources | planned | Planned |
| Verification Engine | Resolve candidate status, freshness, conflicts, expiry | planned | Planned |
| Application Assistant | Prepare truthful materials and human-gated application state | planned | Planned |
| Model Registry / Benchmark | Evidence-based capability classification | planned | Planned |
| Task Runner / AI Worker | Execute low-risk repeatable work with usage records | planned | Planned |
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
Provider Adapter
        ↓
FREE_ONLY Router
        ↓
Capability-aware model selection
        ↓
AI task/worker
        ↓
Usage + remaining + expiry + audit record
```

TASK-002 implements a safe local vertical slice around review, eligibility, inventory, adapter contracts and routing. Discovery, real inventory refresh, live routed invocation, benchmark promotion, and worker execution remain future phases.

## Interfaces / contracts

- Catalog records remain machine-readable and validated; schema evolution must be backward-aware and tested.
- Verified offer claims require official evidence and freshness metadata.
- Eligibility triage is advisory only and must expose blockers/warnings/positives instead of claiming provider approval.
- Real profile and inventory state belong in ignored local files or other approved private storage, not committed public data.
- Credits inventory explicitly distinguishes `billing_state` and `quota_state`; unknown is unsafe.
- Provider adapters expose credential, region, quota, model, cost, invoke and redaction contracts. The Alibaba prototype deliberately refuses live invocation because offline quota/cost are unknown.
- `FREE_ONLY` routing accepts only confirmed-free billing states and confirmed-usable quota states, rejects expired/exhausted/unknown states, enforces minimum capability tier, and hard-stops when no safe route exists.
- Optional AI catalog review produces advisory Artifacts only. Dry-run sends no request; invoke mode is explicit and bounded and never mutates catalog data.
- Human-gated application states must be explicit rather than simulated as successful automation.
- Future task execution should record provider/model/time/token-or-usage information when safely available, free-status evidence, result, output artifact, and review requirement.

## External dependencies

- Provider public documentation, pricing/free-tier/program pages, official APIs, and consoles are external sources whose terms/state can change.
- GitHub Actions is used for CI and selected manual jobs.
- Provider credentials, when required, remain in secure environment/secret storage and never in committed state.
- TASK-002 CI is offline with respect to provider APIs. The manual AI catalog-review workflow exposes the API secret only in explicit `invoke` mode.

## Security and privacy boundaries

- No secrets or identity/payment data in committed state or logs.
- Unknown billing or quota state is unsafe by default.
- Provider calls require an explicitly authorized path; normal CLI/CI prototype flows do not invoke providers.
- Login, OAuth, CAPTCHA/verification, SMS/TOTP, identity/student verification, payment methods, potentially paid service enablement, and final submission require human takeover.
- Application assistance may improve truthful wording but may not invent eligibility facts.
- AI review output cannot automatically promote, edit or commit catalog records.

## Testing strategy

- Structural workflow state: `python scripts/check_ai_state.py`
- Catalog validation: `credits-radar validate`
- Regression/unit/integration tests: `python -m unittest discover -s tests -v`
- Offline vertical smoke flow: `review`, `eligibility`, `inventory`, `route`, and AI-review `dry-run` commands run in `.github/workflows/ci.yml`.
- AI/provider invoke modes are intentionally excluded from PR validation.
- Future live router/provider code must add failure-path tests for unknown quota, exhausted quota, rate limits, paid-risk states, no-paid-fallback behavior, request caps, and redaction.

## Technical debt / known constraints

- Current catalog schema predates the full candidate → verified lifecycle and structured eligibility fields; future schema evolution should be staged rather than destructive.
- Eligibility triage currently uses explicit program type plus transparent text signals; it is intentionally conservative and not a substitute for provider-specific structured eligibility parsers.
- The inventory is local JSON and is not yet refreshed from provider consoles/APIs.
- The Alibaba adapter is configuration-only; live invocation remains the existing manual smoke-test path until a future task can prove quota/billing safeguards programmatically.
- Capability tiers are accepted as inventory facts but are not yet produced by a benchmark engine.
- Discovery, application-state automation, live multi-provider routing, AI workers, and orchestration dashboard remain planned.
