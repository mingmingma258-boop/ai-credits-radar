# Project

- **Project ID:** P001
- **Project name:** AI Credits Radar

## One-line purpose

Build an auditable system that discovers, verifies, evaluates, assists with, and progressively integrates legitimate free AI API, GPU, cloud, developer, education, and research resources into a safe free-only compute workflow.

## Desired outcome

Evolve the existing AI Credits Radar MVP from an auditable credits catalog into a staged platform for discovery, verification, eligibility matching, application assistance, credits inventory, provider integration, free-only routing, capability-aware model selection, and low-risk AI workers — without bypassing provider rules or silently creating paid usage.

## In scope

- Auditable catalog of free/free-credit AI API, GPU, cloud, notebook, developer, student, research, startup, and related resources.
- Official-source verification, freshness tracking, deduplication, change detection, expiration handling, and candidate → verified lifecycle.
- Eligibility/risk assessment using user-supplied truthful profile facts without committing sensitive identity data.
- Application assistance that prepares materials/steps and pauses for human-controlled authentication, verification, payment, and final submission.
- Credits inventory, expiry/use tracking, provider health, and future usage optimization.
- Provider adapters, unified invocation contracts, free-only routing, and hard-stop billing safeguards.
- Model capability registry and later low-cost benchmark-based S/A/B/Unknown classification.
- Low-risk repeatable AI tasks and automation using confirmed free resources.
- Python CLI, JSON/Markdown reports, GitHub Actions, and incremental UI improvements.

## Out of scope

- Circumventing product limits, regional restrictions, CAPTCHAs, identity checks, payment confirmation, provider terms, or account controls.
- Fabricating student, company, startup, research, location, eligibility, quota, or approval information.
- Storing passwords, API secrets, cookies, SMS/TOTP codes, identity-document numbers/images, payment-card data, or other sensitive credentials in committed state.
- Automatic paid fallback when free quota is exhausted or uncertain.
- Automatic final application submission, subscription/plan upgrades, billing changes, or payment-method actions without explicit human control.
- Rewriting the existing MVP from scratch when incremental changes can preserve working catalog/CLI/test behavior.
- Prematurely building a complex web platform before the underlying catalog, safety, provider, and routing contracts are stable.

## Users / stakeholders

- Owner: human project owner
- Primary user: individual developer/research/student user seeking legitimate free AI resources
- Contributors/reviewers: Regular Chat, Codex/Work, and human reviewers

## Hard constraints

- `FREE_ONLY` is the default runtime principle; no paid fallback without a separate explicit human-authorized change.
- Unknown cost/quota state is treated as unsafe, not free.
- Verified resource claims require official evidence; unconfirmed discoveries remain candidate/unverified.
- Provider amount, token, expiry, regional availability, and eligibility can change and must be presented as conditional on current official provider state.
- Human takeover is mandatory for login/OAuth, verification, identity/student proof, payment methods, potentially paid enablement, and final submission.
- No secrets or private credentials in committed state or logs.
- Existing working product behavior and quality checks should be preserved and extended incrementally.

## Success criteria

- [x] Existing repository provides a working auditable catalog, CLI, tests, and manual Alibaba Cloud smoke test baseline.
- [ ] Public-source discovery and change monitoring can produce reviewable candidate/diff reports.
- [ ] Candidate offers can be promoted to verified only with official-source evidence and freshness metadata.
- [ ] Eligibility/application assistance clearly separates automated preparation from mandatory human takeover.
- [ ] Credits inventory can track remaining/used/expiry/provider availability without storing secrets.
- [ ] Provider adapters enforce credential redaction and free/billing safeguards.
- [ ] Unified routing can choose confirmed free resources and hard-stop when no safe free route exists.
- [ ] Model capability tiers are based on evidence/benchmarking rather than provider marketing alone.
- [ ] Low-risk repeatable tasks can use the free compute pool with auditable usage records.

## Source-of-truth rule

This repository is authoritative for P001's versioned product facts, architecture, decisions, tasks, review findings, and handoffs. Chat history and the AI Workflow Hub may route to this repository, but must not replace project-local durable state.
