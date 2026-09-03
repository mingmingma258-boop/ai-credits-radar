# Decisions

Use short ADR-style entries for durable decisions that future sessions must not rediscover.

## ADR-001 — Existing repository is the P001 source of truth

- **Status:** ACCEPTED
- **Decision:** Continue developing the existing `ai-credits-radar` repository incrementally as project P001 rather than creating a replacement repository or rewriting the MVP from scratch.
- **Why:** The repository already has working catalog data, CLI, tests, documentation, web output, CI, and an Alibaba smoke test.
- **Consequences:** New work must read and preserve existing behavior unless a task explicitly approves a breaking migration.

## ADR-002 — Official-source evidence gates verification

- **Status:** ACCEPTED
- **Decision:** Automatically discovered or weakly supported offers remain candidate/unverified; `verified` claims require current official provider evidence.
- **Why:** Free-credit programs change frequently and secondary sources can be stale or misleading.
- **Consequences:** Discovery and verification are separate stages; lack of confirmation is represented explicitly rather than guessed.

## ADR-003 — FREE_ONLY and no-paid-fallback are defaults

- **Status:** ACCEPTED
- **Decision:** Runtime/provider routing must default to free/free-credit resources only and must hard-stop rather than silently fall back to paid usage.
- **Why:** Avoid accidental billing and preserve the product's core purpose.
- **Consequences:** Unknown cost/quota state is treated as unsafe; future paid-mode support, if ever added, requires a separate explicit human-approved design.

## ADR-004 — Human takeover for consequential application/account steps

- **Status:** ACCEPTED
- **Decision:** Login, OAuth, CAPTCHA/verification, SMS/TOTP, identity/student verification, payment methods, paid enablement, and final application submission are human-controlled steps.
- **Why:** These actions are sensitive, consequential, or provider-controlled.
- **Consequences:** Automation should prepare, navigate, explain, save drafts when safely supported, and enter a clear `WAITING_FOR_HUMAN` state instead of bypassing controls.

## ADR-005 — Truthful eligibility only

- **Status:** ACCEPTED
- **Decision:** Application/eligibility assistance may optimize the wording of truthful user-provided facts but may not fabricate identity, location, student/company/startup/research status, account history, or approval state.
- **Why:** Legal/terms compliance and reliable eligibility decisions require factual inputs.
- **Consequences:** Missing facts remain unknown and may require user confirmation; no synthetic qualification.

## ADR-006 — CLI/data/Actions before complex web architecture

- **Status:** ACCEPTED
- **Decision:** Prefer Python CLI, structured JSON, Markdown reports, tests, and GitHub Actions for early phases; expand the web UI only after underlying data/safety/provider contracts stabilize.
- **Why:** This keeps early work testable, auditable, and inexpensive to maintain.
- **Consequences:** Dashboard work is not a priority if core discovery/verification/provider safety remains incomplete.

## ADR-007 — Capability tiers require evidence

- **Status:** ACCEPTED
- **Decision:** New/unknown models should remain `Unknown` until supported by credible evidence or a low-cost benchmark across relevant capabilities; do not classify solely by parameter count or marketing.
- **Why:** The target S/A/B tiers represent task capability, not model size.
- **Consequences:** Tier-aware routing is a later phase after a benchmark/evidence framework exists.

## ADR-008 — Strongest reasoning for Chat, cheapest sufficient executor

- **Status:** ACCEPTED
- **Decision:** When model selection is available, Regular Chat should prefer the strongest available reasoning model for architecture, audit, planning, and review; Codex/Work should prefer the lowest-cost available model that can reliably meet the bounded task's acceptance criteria and validation, escalating only when necessary.
- **Why:** Planning/review quality has high leverage, while bounded execution can often be completed with lower agentic usage when requirements and tests are explicit.
- **Consequences:** Executor cost optimization must never remove required tests, correctness, security, or safety checks. Model names are not hard-coded because availability and usage economics can change.

## ADR-009 — Provider API execution is opt-in per task

- **Status:** ACCEPTED
- **Decision:** Background/catalog tasks do not invoke provider models by default. Any real provider API call must be explicitly authorized by the active task with relevant safety caps; the existing Alibaba smoke test remains manually triggered unless separately changed.
- **Why:** Provider calls can consume quota and may have billing implications.
- **Consequences:** Discovery/review automation should default to public-source processing and dry/report-only behavior.
