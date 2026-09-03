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

---

## Review target — TASK-003

- Project: P001
- Task: TASK-003 — Live FREE_ONLY gateway and bounded AI worker
- Commit / PR: PR #3 (`task/TASK-003-live-free-worker` → `main`)
- Initial reviewed implementation head before review fixes: `0d33d53da875ebeba4713bb90d53309a617ccd28`
- Reviewed fix head: `1a315fe4bd56a68aede06314f3690e65a49c7663`
- Reviewer: Regular Chat
- Date: 2026-09-03
- CI observed before findings: `quality` run #89 job `validate` = `success`; `AI state check` run #26 = `success`
- Review-fix validation: `quality` run #103 job `validate` = `success`, including the complete offline flow; `AI state check` run #33 = `success`

## Findings

### REV-003 — Direct invoke prompt has no global input-size cap

- **Status:** FIXED
- **Severity:** P2
- **Evidence:** Initial `gateway.invoke_free_only()` validated only that `prompt` was non-empty; output tokens were capped but input length was not.
- **Problem:** A very large direct prompt could consume a disproportionate amount of a scarce free quota in one otherwise-safe request.
- **Impact:** FREE_ONLY prevents billing fallback but does not protect the user's free allocation from accidental oversized input consumption.
- **Resolution:** Added a 50,000-character gateway prompt cap and reduced Worker repository context to 30,000 characters so task/instruction/context packaging stays below the gateway boundary.
- **Acceptance check:** `test_oversized_prompt_stops_before_adapter` proves an oversized prompt is rejected before the fake adapter receives any call; quality run #103 succeeded.

### REV-004 — Local worker can allowlist untracked `.local.*` state files

- **Status:** FIXED
- **Severity:** P2
- **Evidence:** Initial Worker path validation confined paths to repository root and allowed safe text suffixes, but did not exclude filenames such as `data/profile.local.json` or `data/credits_inventory.local.json`.
- **Problem:** A user could accidentally include ignored personal/local state as model context.
- **Impact:** Private profile/resource metadata could be sent to a provider despite the Worker being intended for repository context only.
- **Resolution:** Worker context now hard-blocks `.local.` filenames plus `.git` and `artifacts` paths before file existence/content is inspected.
- **Acceptance check:** `test_worker_rejects_local_private_context_even_when_allowlisted` covers the local-state case; ordinary tracked source context remains covered by Worker dry-run; quality run #103 succeeded.

### Final review result

_No remaining P0/P1/P2/P3 findings. PR #3 keeps all automatic CI provider-offline, requires explicit FREE_ONLY live attestation, caps one provider request and input/output size, blocks direct adapter calls, treats Alibaba free-tier exhaustion as a hard stop, scopes the provider secret only to the manual live Action step, and keeps the AI Worker Artifact-only with no repository write or shell authority._

## Finding template

### REV-XXX — Short title

- **Status:** NEW
- **Severity:** P2
- **Evidence:** file/path:line, result, or diff reference
- **Problem:** Concrete defect or requirement mismatch.
- **Impact:** What can go wrong.
- **Requested fix:** Smallest acceptable correction.
- **Acceptance check:** How to verify the fix.
