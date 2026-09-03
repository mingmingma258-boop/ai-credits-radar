# Review

Finding statuses: `NEW`, `ACCEPTED`, `QUESTION`, `REJECTED`, `FIXED`.
Severity: `P0`, `P1`, `P2`, `P3`.

## Review target — TASK-001

- Project: P001
- Task: TASK-001 — Bootstrap P001 AI workflow state
- Commit / PR: PR #1 (`task/TASK-001-bootstrap-ai-workflow` → `main`)
- Reviewed synchronized head before completion-state updates: `8652c431137d8532c8ae0338379f109bd63b46e7`
- Reviewer: Regular Chat
- Date: 2026-09-03
- CI observed: existing `quality` run #27 = `success`; `AI state check` run #3 = `success`

## Findings

_No P0/P1/P2/P3 findings. The PR adds only the approved coordination/workflow layer, does not modify pre-existing product/catalog/provider files, preserves the existing quality workflow, introduces an independent state check, clearly distinguishes implemented vs planned architecture, and encodes FREE_ONLY, human-takeover, truthful-eligibility, official-evidence, and capability/cost-based model-selection rules without hard-coding mutable product model names._

---

## Review target — TASK-002

- Project: P001
- Task: TASK-002 — Build safe end-to-end prototype
- Commit / PR: PR #2 (`task/TASK-002-vertical-prototype` → `main`)
- Reviewed implementation head: `be1a5586910d8789f41e1c2a9b9f5a5d423b608d`
- Reviewer: Regular Chat
- Date: 2026-09-03
- CI observed before review fixes: `quality` run #54 = `success`; `AI state check` run #16 = `success`

## Findings

### REV-001 — Workflow model input is interpolated into shell script

- **Status:** ACCEPTED
- **Severity:** P2
- **Evidence:** `.github/workflows/ai-catalog-review.yml` passes `--model "${{ inputs.model }}"` inside `run:` shell blocks for both dry-run and invoke paths.
- **Problem:** A free-text workflow-dispatch input is substituted into a shell program before execution. Shell metacharacters or command substitution in that input could be interpreted by the runner instead of being treated purely as model data.
- **Impact:** A manually triggered workflow could execute unintended shell commands under the workflow runner context; invoke mode also has access to the provider secret in its step.
- **Requested fix:** Do not interpolate the model input into `run:`. Keep it in the Actions `env` channel (`DASHSCOPE_MODEL`) and let the Python script read its existing environment-backed default.
- **Acceptance check:** Workflow `run:` blocks contain no `${{ inputs.model }}` interpolation, while model selection still reaches the script through `DASHSCOPE_MODEL`; CI remains green.

### REV-002 — Explicit “no credit card required” text produces a payment warning

- **Status:** ACCEPTED
- **Severity:** P2
- **Evidence:** `src/ai_credits_radar/eligibility.py` warns whenever combined catalog text contains `credit card` or `payment method`, without recognizing negated phrases. Existing catalog records include wording such as “no credit card is required”.
- **Problem:** The heuristic can invert a key eligibility/safety fact and report that payment/card verification may be requested even when the catalog explicitly says no card is required.
- **Impact:** The user can receive misleading triage on a core product preference (no-card/free-first opportunities), reducing trust in eligibility ranking.
- **Requested fix:** Add conservative negation handling for explicit no-card/no-payment-method phrases before emitting the payment warning, and add a regression test.
- **Acceptance check:** A synthetic program containing “no credit card is required” does not emit the payment/card warning, while positive payment-required wording still can.

## Finding template

### REV-XXX — Short title

- **Status:** NEW
- **Severity:** P2
- **Evidence:** file/path:line, result, or diff reference
- **Problem:** Concrete defect or requirement mismatch.
- **Impact:** What can go wrong.
- **Requested fix:** Smallest acceptable correction.
- **Acceptance check:** How to verify the fix.
