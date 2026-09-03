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
- Initial reviewed implementation head: `be1a5586910d8789f41e1c2a9b9f5a5d423b608d`
- Reviewed fix head: `2899d4ead96b1f19068e3db649e784b5472117ee`
- Reviewer: Regular Chat
- Date: 2026-09-03
- CI before findings: `quality` run #54 = `success`; `AI state check` run #16 = `success`
- Review-fix validation: `quality` run #62 job `validate` = `success` including tests and offline prototype flow; `AI state check` run #20 = `success`

## Findings

### REV-001 — Workflow model input is interpolated into shell script

- **Status:** FIXED
- **Severity:** P2
- **Evidence:** Initial `.github/workflows/ai-catalog-review.yml` passed `--model "${{ inputs.model }}"` inside `run:` shell blocks.
- **Problem:** A free-text workflow-dispatch input was substituted into a shell program before execution.
- **Impact:** Shell metacharacters could be interpreted by the runner; invoke mode also has access to the provider secret in its step.
- **Resolution:** Removed the input from shell command text. Model choice now reaches the script only through the Actions environment variable `DASHSCOPE_MODEL`; the provider secret remains scoped only to the explicit invoke step. Added a static workflow safety regression test.
- **Acceptance check:** `tests/test_prototype.py` asserts the environment mapping exists and `--model "${{ inputs.model }}"` does not; quality run #62 succeeded.

### REV-002 — Explicit “no credit card required” text produces a payment warning

- **Status:** FIXED
- **Severity:** P2
- **Evidence:** Initial `eligibility.py` matched any `credit card` / `payment method` phrase without recognizing explicit negation.
- **Problem:** The heuristic could invert a key no-card fact.
- **Impact:** Core free/no-card opportunity triage could become misleading.
- **Resolution:** Payment signals are now evaluated per catalog text fragment with conservative no-card/no-payment-method negation handling. A separate explicit positive payment requirement still triggers a warning.
- **Acceptance check:** Regression tests cover both `No credit card is required` (no payment warning) and `payment verification may be requested` (warning retained); quality run #62 succeeded.

### Final review result

_No remaining P0/P1/P2/P3 findings after the accepted fixes. The reviewed prototype preserves existing catalog behavior, keeps provider use opt-in, maintains human takeover boundaries, and implements FREE_ONLY routing as a fail-closed local control plane rather than a paid or uncertain fallback._

## Finding template

### REV-XXX — Short title

- **Status:** NEW
- **Severity:** P2
- **Evidence:** file/path:line, result, or diff reference
- **Problem:** Concrete defect or requirement mismatch.
- **Impact:** What can go wrong.
- **Requested fix:** Smallest acceptable correction.
- **Acceptance check:** How to verify the fix.
