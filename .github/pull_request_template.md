## Work order

- Project: `P001`
- Task: `TASK-XXX`
- Work Type: `PLAN | CODE | RESEARCH | ARTIFACT | OPS | REVIEW`
- Source of truth read: `AGENTS.md` + relevant `_ai/` state

## Goal

Describe the bounded outcome this PR is intended to achieve.

## Scope

### In scope

- 

### Out of scope

- 

## Acceptance criteria

- [ ] Matches the approved task acceptance criteria.
- [ ] No unrelated refactor or scope expansion.

## Validation

- [ ] `python scripts/check_ai_state.py`
- [ ] Relevant project validation/tests from the active task
- [ ] Existing quality checks preserved where applicable

## Safety / cost

- [ ] No secrets or sensitive identity/payment data committed or logged.
- [ ] No paid fallback or unknown-cost provider path introduced without explicit human authorization.
- [ ] No login/OAuth/verification/payment/final application submission was automated outside an explicitly approved human-gated design.
- [ ] Any real provider API call was explicitly authorized by the task and used bounded safety caps.

## Handoff

- `_ai/STATUS.md` updated: yes / no / not applicable
- `_ai/HANDOFF.md` updated with this PR reference: yes / no
- Review findings fixed only when marked `ACCEPTED`: yes / not applicable

## Notes for reviewer

Call out assumptions, known limitations, and any human action still required.
