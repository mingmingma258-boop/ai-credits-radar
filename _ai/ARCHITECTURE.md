# Architecture

## Current state

P001 already has a working MVP. The current repository contains an auditable JSON catalog, Python package/CLI, standard-library unit tests, a static web view, application guidance, CI, and a manually triggered Alibaba Cloud Model Studio smoke test. The workflow layer introduced by TASK-001 is coordination metadata only and must not replace those working components.

## Components

| Component | Responsibility | Key paths / systems | State |
|---|---|---|---|
| Catalog data | Auditable provider/program records | `data/programs.json` | Implemented |
| Catalog/validation logic | Load, validate, filter, sort, search records | `src/ai_credits_radar/catalog.py` | Implemented |
| CLI | Human-facing catalog commands | `src/ai_credits_radar/cli.py` | Implemented |
| Quality tests | Catalog/CLI regression checks | `tests/` | Implemented |
| Static web view | Lightweight browsing | `web/` | Implemented |
| Application guidance | Human-safe application playbook | `docs/application-playbook.md` | Implemented |
| Alibaba smoke test | Manual minimal provider connectivity check | `scripts/aliyun_bailian_smoke_test.py`, `.github/workflows/aliyun-smoke-test.yml` | Implemented |
| Discovery Engine | Find public candidate offers from official/public sources | planned | Planned |
| Verification Engine | Resolve candidate status, freshness, conflicts, expiry | planned | Planned |
| Eligibility/Application Assistant | Match truthful profile facts and prepare human-gated applications | planned | Planned |
| Credits Inventory | Track granted resource, usage, remaining, expiry, availability | planned | Planned |
| Provider Adapter layer | Normalize credential/quota/model/invocation/safety contracts | planned | Planned |
| Model Registry / Benchmark | Evidence-based capability classification | planned | Planned |
| Free-Only Router | Route only to confirmed safe free/free-credit paths | planned | Planned |
| Task Runner / AI Worker | Execute low-risk repeatable work with audit records | planned | Planned |
| Notification/Dashboard | Surface new/changed/expiring/blocked state | planned | Planned |

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
Free-Only Router
        ↓
Capability-aware model selection
        ↓
AI task/worker
        ↓
Usage + remaining + expiry + audit record
```

The system should evolve through this flow incrementally. A later component must not be treated as already implemented merely because it appears in the architecture.

## Interfaces / contracts

- Catalog records remain machine-readable and validated; schema evolution must be backward-aware and tested.
- Verified offer claims require official evidence and freshness metadata.
- Provider adapters should eventually expose contracts equivalent to credential check, region check, quota check, model listing, invocation, cost/risk estimate, paid-usage disable/stop, and log redaction.
- `FREE_ONLY` routing must fail closed when cost/quota safety is unknown.
- Human-gated application states must be explicit rather than simulated as successful automation.
- Task execution should record provider/model/time/token-or-usage information when safely available, free-status evidence, result, output artifact, and review requirement.

## External dependencies

- Provider public documentation, pricing/free-tier/program pages, official APIs, and consoles are external sources whose terms/state can change.
- GitHub Actions is used for CI and selected manual/periodic jobs.
- Provider credentials, when required, must remain in secure environment/secret storage and never in committed state.

## Security and privacy boundaries

- No secrets or identity/payment data in committed state or logs.
- Unknown billing state is unsafe by default.
- Provider calls require an explicitly authorized task; background discovery should not invoke paid/free model APIs unless explicitly enabled.
- Login, OAuth, CAPTCHA/verification, SMS/TOTP, identity/student verification, payment methods, potentially paid service enablement, and final submission require human takeover.
- Application assistance may improve truthful wording but may not invent eligibility facts.

## Testing strategy

- Structural workflow state: `python scripts/check_ai_state.py`
- Existing catalog validation: `credits-radar validate`
- Existing regression tests: `python -m unittest discover -s tests -v`
- CI: preserve `.github/workflows/ci.yml`; add an independent AI-state check rather than replacing quality CI.
- Provider calls: use minimal, explicitly authorized tests with strict time/token/request caps and sanitized errors.
- Future router/provider code: include failure-path tests for unknown quota, exhausted quota, rate limits, paid-risk states, and no-paid-fallback behavior.

## Technical debt / known constraints

- Current catalog schema predates the full long-term product model and will need staged evolution rather than a destructive rewrite.
- Current provider integration is intentionally narrow (manual Alibaba smoke test), not yet a general adapter layer.
- Automated discovery, inventory, routing, benchmark, and worker layers are future work and must not be represented as complete.
