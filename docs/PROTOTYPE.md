# AI Credits Radar — Product Design and Vertical Prototype

This document is the durable product design for the first end-to-end prototype. It separates **implemented prototype behavior** from **planned production behavior** so future sessions do not mistake architecture for working functionality.

## 1. Product objective

AI Credits Radar should turn legitimate provider free resources into an auditable workflow:

```text
Discover → Verify → Triage eligibility → Prepare application → Human takeover
        → Register granted credits → Provider adapter → FREE_ONLY router
        → Capability-aware task execution → Usage / expiry / audit record
```

The core safety invariant is fail-closed: unknown price, quota, account state, or provider terms are **not** treated as free.

## 2. Product layers

| Layer | Responsibility | Prototype state |
|---|---|---|
| Catalog | Store auditable opportunities with provider evidence | Existing / preserved |
| Catalog Review | Detect schema issues, stale verification, human handoff, billing warnings | Implemented offline |
| Discovery / Verification | Find new official-source candidates and confirm current terms | Designed; crawler/parser not yet implemented |
| Eligibility | Explain likely/possible/not-match based on non-sensitive profile facts | Implemented as transparent triage |
| Application Assistant | Prepare materials and pause for consequential steps | Designed; current playbook remains human-driven |
| Credits Inventory | Track safe-to-use granted resources, quota state, expiry, model availability | Implemented local JSON prototype |
| Provider Adapter | Normalize credential/region/quota/models/cost/invoke/redaction contracts | Contract implemented; Alibaba offline config adapter implemented |
| FREE_ONLY Router | Select confirmed-safe free resources and hard-stop otherwise | Implemented local prototype |
| Model Registry / Benchmark | Evidence-based S/A/B/Unknown capability classification | Designed; not yet benchmarked |
| AI Worker | Execute low-risk tasks and record usage | Designed; not yet connected to live routing |
| Dashboard / Notifications | Surface new, expiring, blocked, running state | Existing static catalog only; orchestration dashboard planned |

## 3. Domain model

### Program

The existing `data/programs.json` remains the opportunity catalog. It describes what a provider publicly offers, not what the user already owns.

Important lifecycle distinction:

```text
candidate/unverified → manually verified from current official evidence → usable application target
```

The legacy catalog currently represents availability through `active`, `conditional`, and `verify-before-apply`. Future schema evolution should add explicit verification lifecycle fields without destructive migration.

### UserProfile

A local profile stores only routing/eligibility facts needed for triage, for example region and boolean capabilities. The prototype deliberately rejects arbitrary extra fields so a committed/example profile does not grow into a store for names, school records, IDs, phone numbers, credentials, or payment details.

The eligibility result is always non-authoritative:

- `likely`: no explicit blocker was found in the local structured signals;
- `possible`: provider review, region, identity, payment, or conditional terms require confirmation;
- `not_match`: an explicit role/requirement conflicts with the profile.

Provider pages remain authoritative.

### CreditResource

A granted/available resource is distinct from a catalog opportunity. The inventory tracks:

- provider and resource type;
- `free_only` intent;
- billing state;
- quota state and optional remaining amount/unit;
- status and expiry;
- enabled models and evidence-based capability tier;
- routing priority.

Real user inventory belongs in a local ignored file, not the public repository.

### RouteDecision

The router outputs either `selected` with a provider/resource/model that passes all safety gates, or `hard_stop` with explicit rejection reasons. There is no paid fallback in the prototype.

## 4. FREE_ONLY routing contract

A route is eligible only when all of the following hold:

1. requested resource type matches;
2. `free_only == true`;
3. billing state is explicitly `free_tier_confirmed` or `free_quota_confirmed`;
4. quota state is `confirmed_available` or `ongoing_free_tier`;
5. resource status is `available`;
6. remaining numeric quota, if known, is greater than zero;
7. expiry has not passed;
8. at least one enabled model satisfies the minimum tier.

Selection policy:

1. choose the least-capable model that still satisfies the requested tier;
2. prefer resources that expire sooner, avoiding wasted credits;
3. use explicit inventory priority as the next tie-breaker.

Unknown billing or unknown quota is rejected even when a resource looks attractive.

## 5. Provider adapter contract

A future live adapter follows one interface:

```text
check_credentials()
check_region()
check_quota()
list_models()
estimate_cost()
invoke()
redact_logs()
```

The prototype Alibaba adapter is intentionally offline. It can confirm whether environment configuration exists and redact the secret, but it reports quota/cost as unknown and refuses live invocation. Existing manual smoke testing remains the approved connectivity path.

Future live adapters must add provider-specific safety evidence before `invoke()` becomes routable.

## 6. Catalog review paths

### Offline review

`credits-radar review` is deterministic and performs no network/model call. It reports catalog validation errors, status/kind counts, stale `last_verified` records, human-handoff requirements, billing/payment attention markers, verify-before-apply records, and evidence-type markers that do not contain `official`.

### Optional AI review

The `AI catalog review` GitHub workflow is `workflow_dispatch` only and defaults to `dry-run`.

`dry-run` validates the catalog, creates the deterministic report, prepares the AI review input, sends no provider request, and uploads the Markdown artifact.

`invoke` is an explicit human choice, uses the existing `DASHSCOPE_API_KEY` secret, caps completion tokens, withholds HTTP error bodies, asks the model to use only supplied catalog facts, uploads advisory Markdown only, never edits catalog data, and never commits.

Before choosing `invoke`, the human should confirm the selected model has safe free quota and relevant auto-stop/billing safeguards in the provider console.

## 7. Application automation boundary

Automation may eventually organize provider requirements, draft truthful project/use-case wording, prepare checklists, open public information pages, and save non-sensitive draft state where provider tooling safely supports it.

It must enter `WAITING_FOR_HUMAN` for login/OAuth, CAPTCHA/SMS/TOTP, identity/student verification, identity-document upload, payment method or billing enablement, potentially paid service activation, and final application submission.

No identity, student, company, startup, research, region, funding, or approval fact may be invented.

## 8. Model capability design

Capability tier is a task-routing signal, not parameter count.

```text
Unknown → mini benchmark / evidence → B / A / S
```

Planned dimensions include coding, reasoning, instruction following, structured output, tool calling, agent behavior, long context, latency/reliability, and real project tasks. Until evidence exists, models stay `Unknown`.

The prototype inventory accepts S/A/B/Unknown but does not benchmark or promote a model automatically.

## 9. Planned discovery engine

The next discovery implementation should use provider-specific source definitions instead of an unrestricted crawler. A source definition should record provider, canonical official URLs, allowed source type, public-only authentication policy, parser/extractor strategy, rate limit/timeout, last successful observation, and content/evidence fingerprint.

Discovery outputs candidates and diffs. It must not directly promote a candidate to verified or submit an application.

## 10. Planned AI Worker

A future worker consumes a bounded task contract with task type, minimum tier, request/token caps, `free_only`, and human-review requirements.

```text
Task → Router → safe provider/model → bounded invoke → usage record
     → retry another confirmed-free route if allowed
     → HARD STOP when no safe route remains
```

Every run should record provider, model, time, usage/tokens when available, free-status evidence, result, artifact path, retry/fallback decision, and review requirement.

## 11. Repository data policy

Committed: public provider catalog, synthetic example profile/inventory, schemas/rules/tests/reports without secrets, and product design/workflow state.

Ignored/local or secret storage: real personal profile details, actual private balances, API keys/tokens/cookies, identity/student documents, phone/payment data, and authentication codes.

## 12. Prototype demo

```bash
credits-radar validate
credits-radar review --output /tmp/catalog-review.md
credits-radar eligibility --profile data/profile.example.json --json
credits-radar inventory --inventory data/credits_inventory.example.json --json
credits-radar route --inventory data/credits_inventory.example.json --tier A --json
python scripts/ai_catalog_review.py --mode dry-run --output /tmp/ai-catalog-review.md
```

These commands demonstrate the control plane without provider/API side effects.

## 13. Next implementation phases

1. **Discovery + verification:** source registry, public-source probes/parsers, candidate snapshots, catalog diff reports.
2. **Application records:** local application-state schema and truthful material generator with explicit human gates.
3. **Real inventory ingestion:** user-confirmed balances/expiry and provider health refresh without committing secrets.
4. **Provider adapters:** Alibaba first, then a small number of high-value free API providers; every adapter must prove billing/quota safety before invocation.
5. **Model registry/benchmark:** low-cost evidence collection and tier assignment.
6. **Worker/runtime:** bounded tasks, usage ledger, retry/fallback within FREE_ONLY pool.
7. **Dashboard/notification:** only after underlying state contracts are stable.

The order is intentional: discovery and safety evidence must mature before a general live router/worker can be trusted.
