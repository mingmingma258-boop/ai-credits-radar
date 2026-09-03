# Agent Instructions

This repository is the source of truth for project **P001 — AI Credits Radar**.

## Read first

Before changing files, read:
1. `_ai/PROJECT.md`
2. `_ai/ARCHITECTURE.md`
3. `_ai/DECISIONS.md`
4. `_ai/TASKS.md`
5. `_ai/STATUS.md`
6. `_ai/REVIEW.md` when fixing review findings
7. Existing product files relevant to the task before proposing replacements

## Reasoning and executor model policy

- For Regular Chat planning, architecture, audit, and review, prefer the strongest available reasoning model when the product surface allows model selection.
- For Codex/Work execution, prefer the lowest-cost available model that can reliably satisfy the approved acceptance criteria and validation requirements.
- Escalate executor model capability only when task complexity, failed validation, or review evidence shows the cheaper model is insufficient.
- Never reduce required testing, security, correctness, or review quality merely to save usage.
- Model names and pricing/usage behavior may change; follow this policy by capability and verified quality rather than hard-coding one product model name.

## Task selection

- Execute only a task explicitly marked `READY`.
- Keep at most one `READY` task for a normal executor run.
- If more than one `READY` task exists, stop instead of choosing one yourself.
- Verify the task's `Project` field is `P001`.
- Do not silently broaden scope or perform unrelated refactors.
- Prefer the smallest coherent change satisfying acceptance criteria.
- Reuse the existing catalog, CLI, tests, workflows, and project patterns before inventing abstractions.

## Branch and PR policy

- Make repository changes on a non-default task branch.
- Do not push implementation changes directly to the default branch without an explicit human override for that action.
- Open/update a PR when supported and record it in `_ai/HANDOFF.md`.
- Do not merge your own PR unless the human owner explicitly authorizes the merge.

## Product safety boundaries

- Default operating principle is `FREE_ONLY`: never silently fall back from a free/free-credit path to a paid path.
- Unknown billing state is not equivalent to free. Stop and require human confirmation when cost or quota safety cannot be established.
- Do not automatically enable paid services, subscriptions, upgrades, billing, or auto-recharge.
- Do not automatically perform login, OAuth authorization, CAPTCHA/verification, SMS/TOTP, identity verification, student verification, payment-method entry, or final application submission.
- Do not fabricate identity, region, student status, company/startup status, research history, eligibility, quota, official evidence, or approval state.
- Prefer official provider sources for verified offer claims; unconfirmed discoveries remain candidate/unverified.
- Never commit or print credentials, API keys, cookies, access tokens, identity documents, phone numbers, payment details, or generated secrets.
- Provider API calls must be explicitly authorized by the active task. Existing Alibaba smoke testing remains manual unless the human explicitly changes that rule.

## Validation and handoff

Before completion:
- Run the narrowest relevant task checks.
- Run `python scripts/check_ai_state.py`.
- For product-code changes, preserve and run the existing project checks where relevant: `credits-radar validate` and `python -m unittest discover -s tests -v`.
- Update `_ai/STATUS.md` and `_ai/HANDOFF.md`.
- Mark the task `DONE` only when acceptance criteria and required validation are satisfied.
- If validation cannot run, record exactly why.

## Review fixes

Only implement findings explicitly marked `ACCEPTED`. Do not implement `NEW`, `QUESTION`, `REJECTED`, or otherwise untriaged findings.
