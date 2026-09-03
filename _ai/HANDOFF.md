# Handoff

## Task

- Project: P001
- ID: TASK-001
- Status: IN_PROGRESS

## Files / systems changed

- Added project-local AI workflow coordination files only: `AGENTS.md`, `_ai/*`, `scripts/check_ai_state.py`, `.github/workflows/ai-state-check.yml`, and `.github/pull_request_template.md`.
- Existing product/catalog/provider files are intentionally unchanged.

## Behavior / result changed

- Future Chat/Codex/Work sessions can recover P001 goals, architecture, durable decisions, task state, review findings, and handoff from this repository.
- Executor work is bounded by Project ID, Work Type, task status, branch/PR rules, and project safety constraints.
- Model-use strategy is explicit: strongest available Regular Chat reasoning model for planning/audit/review when selectable; lowest-cost Codex/Work model that still reliably satisfies quality and validation, escalating only when necessary.
- No product/runtime behavior change is intended in TASK-001.

## Validation performed

- Existing repository structure, README, quality CI, workflows, and scripts were read before bootstrap changes.
- No provider API call, secret read/write, login, verification, payment, application, or external account action was performed.

## Validation not performed

- Final `python scripts/check_ai_state.py` CI result is pending.
- Existing `quality` CI result on the final bootstrap PR is pending.
- Alibaba smoke test is intentionally not run because provider API calls are out of scope for this task.

## Known limitations

- The durable files summarize project facts and do not reproduce the full historical chat transcript.
- Long-term planned architecture is not the same as implemented functionality; planned components are explicitly marked planned in `_ai/ARCHITECTURE.md`.
- Exact Chat/Codex/Work model names and usage economics can change; durable policy is capability/cost based.

## Follow-up items

- Open the bootstrap PR and write the PR reference back here.
- Wait for AI-state and existing quality CI.
- Perform Regular Chat Review of the actual diff.
- Human decides whether to merge.
- After merge, perform a read-only gap audit and define the first real product `CODE` task; current leading candidate is Manual AI Catalog Review v1, subject to audit.

## Commit / PR

- Task branch: `task/TASK-001-bootstrap-ai-workflow`
- PR/reference: pending creation
