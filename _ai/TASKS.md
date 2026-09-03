# Tasks

Allowed statuses: `DRAFT`, `READY`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `CANCELLED`.

Normally keep only one task `READY` per executor run.

## TASK-001 — Bootstrap P001 AI workflow state

- **Project:** P001
- **Status:** DONE
- **Work type:** CODE
- **Owner:** human
- **Executor:** Regular Chat + GitHub setup
- **Reviewer:** Regular Chat
- **Goal:** Install project-local AI coordination state in the existing AI Credits Radar repository without changing product behavior or triggering provider API usage.

### In scope

- Add project-local `AGENTS.md`.
- Add `_ai/PROJECT.md`, `_ai/ARCHITECTURE.md`, `_ai/DECISIONS.md`, `_ai/TASKS.md`, `_ai/STATUS.md`, `_ai/REVIEW.md`, and `_ai/HANDOFF.md`.
- Add `scripts/check_ai_state.py` based on the Hub project template.
- Add an independent `.github/workflows/ai-state-check.yml` without replacing existing quality/provider workflows.
- Add a PR template for Project/Task/Work Type, acceptance criteria, validation, safety, and handoff.
- Record the durable model-selection policy: strongest available Chat reasoning model for planning/audit/review when selectable; lowest-cost executor model that reliably meets quality/validation, escalating only when necessary.

### Out of scope

- Changing `data/programs.json`, catalog/CLI code, tests, web files, README, application playbook, or existing provider scripts/workflows.
- Implementing AI Catalog Review, discovery, provider adapters, inventory, router, benchmark, dashboard, or AI workers.
- Triggering Alibaba or any other provider API call.
- Modifying GitHub secrets, account/provider settings, billing, plans, applications, or external identity verification.

### Acceptance criteria

- [x] `_ai/PROJECT.md` identifies this repository as P001 with no `PXXX` placeholder.
- [x] Durable project boundary, architecture, safety constraints, and model-use policy are recorded.
- [x] Project-local checker validates Project ID, Work Type, duplicate task IDs, task/project identity, required state files, and single-READY invariant.
- [x] Existing quality CI and Alibaba smoke-test workflow remain unchanged.
- [x] New AI-state workflow runs independently on PR/push-to-main and requires no provider credentials.
- [x] No product behavior, catalog record, provider invocation code, or external account state changes.
- [x] `python scripts/check_ai_state.py` passed in GitHub Actions `AI state check` run #3 on the synchronized review head.
- [x] Existing `quality` CI passed in run #27 on the synchronized review head, including catalog validation and unit tests.
- [x] Regular Chat reviewed PR #1 and recorded no P0/P1/P2/P3 findings.

### Validation

```bash
python scripts/check_ai_state.py
credits-radar validate
python -m unittest discover -s tests -v
```

No provider smoke test was required or permitted for this bootstrap task.

---

## TASK-002 — Build safe end-to-end prototype

- **Project:** P001
- **Status:** DONE
- **Work type:** CODE
- **Owner:** human
- **Executor:** bounded repository executor
- **Reviewer:** Regular Chat
- **Goal:** Turn the existing catalog MVP into a runnable vertical-slice prototype that demonstrates catalog review, truthful eligibility triage, credits inventory, free-only routing, and a manual AI catalog-review workflow without automatically invoking providers or modifying catalog data.

### Context

The post-bootstrap audit confirmed the repository already has a working catalog, CLI, tests, static web view, application guidance, quality CI, and a manual Alibaba smoke test. The highest-value prototype is therefore an incremental orchestration layer rather than a rewrite.

### In scope

- Add an offline catalog review/audit module that produces deterministic Markdown findings for stale verification, human handoff, payment/billing cautions, and catalog health.
- Add a transparent eligibility-triage module driven by a local user-profile JSON file; it may classify likely/possible/not-match but must explain reasons and must not claim official eligibility.
- Add a credits-inventory schema/module with validation and summary; commit only an example inventory and ignore local real inventory/profile files.
- Add a `FREE_ONLY` router that rejects unknown billing/quota states, respects minimum capability tier, prioritizes confirmed-safe resources and earlier expiry, and hard-stops when no safe route exists.
- Add a provider-adapter contract plus a non-network Alibaba configuration adapter sufficient to demonstrate credential/config safety without replacing the existing manual smoke test.
- Extend the CLI with prototype commands for `review`, `eligibility`, `inventory`, and `route` while preserving existing commands.
- Add a manual `AI catalog review` workflow and script. Default mode must be dry-run/report-only; opt-in invoke mode may use the existing `DASHSCOPE_API_KEY`, a bounded token limit, sanitized errors, and upload a Markdown Artifact only. It must not modify or commit `data/programs.json`.
- Add design/prototype documentation, example local-data files, tests, and README usage.
- Correct stale post-merge workflow status from TASK-001.

### Out of scope

- Automatically logging into provider consoles or application sites.
- CAPTCHA, SMS/TOTP, identity/student verification, payment methods, billing changes, or final application submission.
- Automatically invoking Alibaba or any other model/provider in CI, scheduled jobs, or default CLI paths.
- Automatically editing, committing, or promoting catalog records based on AI output.
- Full web dashboard rewrite, production task queue, real multi-provider invocation, automatic discovery crawler, or benchmark-based S/A/B classification.
- Treating heuristic eligibility triage as provider approval or authoritative qualification.

### Acceptance criteria

- [x] Existing `credits-radar list/search/summary/validate` behavior remains compatible.
- [x] `credits-radar review` can generate an offline Markdown catalog health report.
- [x] `credits-radar eligibility --profile <local-json>` returns explained, explicitly non-authoritative triage results without requiring sensitive identity fields.
- [x] `credits-radar inventory --inventory <local-json>` validates and summarizes free-resource holdings without secrets.
- [x] `credits-radar route --inventory <local-json> --tier A` selects only confirmed-safe free resources and returns a hard-stop result when none qualify.
- [x] Unknown billing/quota state is rejected by routing rather than assumed free.
- [x] Example profile/inventory files are clearly synthetic and real local files are ignored by Git.
- [x] Provider-adapter contract exists and Alibaba config checks never print the API key.
- [x] Manual `AI catalog review` workflow defaults to dry-run, uses `workflow_dispatch`, uploads an Artifact, has read-only repository permissions, and never commits changes.
- [x] AI invoke mode is explicit, bounded, sanitized, and was not executed as part of TASK-002 validation.
- [x] New unit tests cover review, eligibility, inventory, routing safety, adapter redaction/config behavior, workflow-input safety, and CLI integration.
- [x] Existing `quality` CI and `python scripts/check_ai_state.py` passed after the accepted review fixes (`quality` run #62 validate job success; `AI state check` run #20 success).
- [x] Regular Chat reviewed PR #2; REV-001 and REV-002 were accepted, fixed, and no P0/P1/P2/P3 findings remain.

### Validation

```bash
python scripts/check_ai_state.py
credits-radar validate
python -m unittest discover -s tests -v
credits-radar review --output /tmp/catalog-review.md
credits-radar eligibility --profile data/profile.example.json --json
credits-radar inventory --inventory data/credits_inventory.example.json --json
credits-radar route --inventory data/credits_inventory.example.json --tier A --json
python scripts/ai_catalog_review.py --mode dry-run --output /tmp/ai-catalog-review.md
```

Provider smoke tests and AI invoke mode were intentionally not run for TASK-002.

---

## TASK-003 — Live FREE_ONLY gateway and bounded AI worker

- **Project:** P001
- **Status:** DONE
- **Work type:** CODE
- **Owner:** human
- **Executor:** bounded repository executor
- **Reviewer:** Regular Chat
- **Goal:** Make P001 ready to safely use a real free-quota model and let that model produce bounded development artifacts for P001, while preserving human review/merge and preventing automatic paid fallback.

### In scope

- Extend the credits inventory with explicit live-use safety attestations: provider id, confirmation timestamp, `free_quota_only`/equivalent stop protection, and per-run token/request caps.
- Add a `FREE_ONLY` gateway that routes first, then performs provider preflight, refuses stale/unknown/unsafe attestations, caps input/output, disables retries, and records sanitized local usage metadata.
- Promote the Alibaba Model Studio adapter from config-only to an explicitly gated live adapter using the OpenAI-compatible endpoint. It may invoke only after the gateway has produced a confirmed-safe route and live-use attestation.
- Treat Alibaba `403 AllocationQuota.FreeTierOnly` as a safe exhaustion stop, not as a retry/fallback signal.
- Add `credits-radar invoke` for explicit one-shot live use and a `--dry-run` path that exercises all repository-side safety gates without sending a request.
- Add a bounded AI Worker v1 that accepts a task JSON plus an allowlist of repository context files, calls the same gateway, and writes reviewable artifacts only; it must not edit files, commit, push, merge, access GitHub secrets, or run shell commands.
- Add a manual GitHub Actions worker workflow whose default is dry-run. Live mode requires explicit per-run confirmations before the provider secret is exposed to the invoking step.
- Add synthetic examples, documentation, regression tests, and offline CI coverage.

### Out of scope

- Triggering a real provider call during TASK-003 implementation or CI.
- Automatically checking or changing Alibaba billing/account/identity settings.
- Automatically deciding that a provider is free from API success alone.
- Automatic provider fallback, paid fallback, retries that can multiply usage, background/scheduled live calls, or autonomous loops.
- Direct AI Worker writes to the repository, shell execution, GitHub write permissions, secret access, PR creation, or merge.
- Multi-provider live routing, automatic quota refresh, benchmark-derived tiers, discovery crawling, or application submission.

### Acceptance criteria

- [x] Live invocation is impossible unless routing safety and explicit recent live-use confirmation both pass.
- [x] Unknown/stale billing or quota state, missing stop protection, expired resource, missing key, unsupported provider, or Tier mismatch hard-stop before a request is sent.
- [x] Alibaba live adapter sends at most one bounded request per `invoke`, has no automatic retry, blocks direct invocation, sanitizes errors, and recognizes `AllocationQuota.FreeTierOnly` as an exhausted/free-only stop.
- [x] `credits-radar invoke --dry-run` reports selected route/preflight without network access or provider secrets.
- [x] Live `credits-radar invoke` requires local inventory confirmation metadata and committed `example=true` inventory can never authorize live use.
- [x] AI Worker reads only explicitly allowlisted repository context, blocks `.local.`/generated/git-internal paths, and writes artifacts only to a caller-selected output directory.
- [x] Gateway/Worker input and output limits prevent unbounded context ingestion and oversized accidental calls.
- [x] Manual Actions worker defaults to dry-run; live step receives the secret only when both free-quota and stop-protection confirmations are true.
- [x] No provider call occurs in unit tests or PR CI; live network behavior is mocked.
- [x] Existing catalog/prototype commands remain compatible; `quality` run #103 passed install, catalog validation, all tests and offline smoke flow; `AI state check` run #33 passed.
- [x] Regular Chat reviewed PR #3; REV-003 and REV-004 were accepted, fixed, and no P0/P1/P2/P3 findings remain.

### Validation

```bash
python scripts/check_ai_state.py
credits-radar validate
python -m unittest discover -s tests -v
credits-radar invoke --inventory data/credits_inventory.example.json --tier A --prompt "hello" --dry-run --json
python scripts/free_ai_worker.py --task data/worker_task.example.json --inventory data/credits_inventory.example.json --dry-run --output-dir /tmp/free-ai-worker
```

No real provider invocation was performed for TASK-003 validation.