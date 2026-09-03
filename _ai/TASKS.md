# Tasks

Allowed statuses: `DRAFT`, `READY`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `CANCELLED`.

Normally keep only one task `READY` per executor run.

## TASK-001 — Bootstrap P001 AI workflow state

- **Project:** P001
- **Status:** IN_PROGRESS
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

- [ ] `_ai/PROJECT.md` identifies this repository as P001 with no `PXXX` placeholder.
- [ ] Durable project boundary, architecture, safety constraints, and model-use policy are recorded.
- [ ] Project-local checker validates Project ID, Work Type, duplicate task IDs, task/project identity, required state files, and single-READY invariant.
- [ ] Existing quality CI and Alibaba smoke-test workflow remain unchanged.
- [ ] New AI-state workflow runs independently on PR/push-to-main and requires no provider credentials.
- [ ] No product behavior, catalog record, provider invocation code, or external account state changes.
- [ ] `python scripts/check_ai_state.py` passes.
- [ ] Existing `quality` CI passes on the bootstrap PR.
- [ ] Regular Chat reviews the final bootstrap diff before human merge.

### Validation

```bash
python scripts/check_ai_state.py
credits-radar validate
python -m unittest discover -s tests -v
```

No provider smoke test is required or permitted for this bootstrap task.
