"""Deterministic catalog review helpers used by CLI and optional AI review."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from .catalog import programs_from, validate_catalog


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def audit_catalog(catalog: dict[str, Any], *, today: date | None = None, stale_days: int = 90) -> dict[str, Any]:
    """Return a deterministic, non-network audit of the current catalog."""

    now = today or date.today()
    programs = programs_from(catalog)
    validation_errors = validate_catalog(catalog)
    stale_before = now - timedelta(days=max(stale_days, 0))

    stale: list[dict[str, str]] = []
    human_handoff: list[str] = []
    billing_attention: list[str] = []
    verify_before_apply: list[str] = []
    nonofficial_evidence: list[str] = []

    for program in programs:
        identifier = str(program.get("id", "(missing-id)"))
        verified = _parse_date(program.get("last_verified"))
        if verified is None or verified < stale_before:
            stale.append({"id": identifier, "last_verified": str(program.get("last_verified", "unknown"))})
        if program.get("handoff") not in {None, "none"}:
            human_handoff.append(identifier)
        risk_text = " ".join(
            str(program.get(field, "")) for field in ("payment_note", "caution", "requirements")
        ).casefold()
        if any(token in risk_text for token in ("billing", "payment", "credit card", "card", "paid", "charge", "recharge")):
            billing_attention.append(identifier)
        if program.get("status") == "verify-before-apply":
            verify_before_apply.append(identifier)
        evidence_type = str(program.get("evidence_type", "")).casefold()
        if "official" not in evidence_type:
            nonofficial_evidence.append(identifier)

    return {
        "generated_on": now.isoformat(),
        "stale_days": stale_days,
        "total": len(programs),
        "validation_errors": validation_errors,
        "status_counts": dict(sorted(Counter(str(p.get("status", "unknown")) for p in programs).items())),
        "kind_counts": dict(sorted(Counter(str(p.get("kind", "unknown")) for p in programs).items())),
        "stale": stale,
        "human_handoff": sorted(human_handoff),
        "billing_attention": sorted(set(billing_attention)),
        "verify_before_apply": sorted(verify_before_apply),
        "nonofficial_evidence": sorted(nonofficial_evidence),
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render an audit result as a reviewable Markdown artifact."""

    lines = [
        "# AI Credits Radar — Catalog Review",
        "",
        f"Generated: `{report['generated_on']}`",
        "",
        "> This is an offline catalog audit. It does not verify live provider terms or user eligibility.",
        "",
        "## Summary",
        "",
        f"- Records: **{report['total']}**",
        f"- Validation errors: **{len(report['validation_errors'])}**",
        f"- Stale verification records (>{report['stale_days']} days): **{len(report['stale'])}**",
        f"- Human-handoff records: **{len(report['human_handoff'])}**",
        f"- Billing/payment-attention records: **{len(report['billing_attention'])}**",
        f"- Verify-before-apply records: **{len(report['verify_before_apply'])}**",
        f"- Records without an `official` evidence type marker: **{len(report['nonofficial_evidence'])}**",
        "",
        "### Status counts",
        "",
    ]
    for key, count in report["status_counts"].items():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "### Kind counts", ""])
    for key, count in report["kind_counts"].items():
        lines.append(f"- `{key}`: {count}")

    def section(title: str, items: Iterable[Any]) -> None:
        entries = list(items)
        lines.extend(["", f"## {title}", ""])
        if not entries:
            lines.append("None.")
            return
        for item in entries:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('id')}` — last verified: `{item.get('last_verified')}`")
            else:
                lines.append(f"- `{item}`")

    section("Validation errors", report["validation_errors"])
    section("Stale verification", report["stale"])
    section("Requires human handoff", report["human_handoff"])
    section("Billing / payment attention", report["billing_attention"])
    section("Verify before apply", report["verify_before_apply"])
    section("Evidence marker review", report["nonofficial_evidence"])
    lines.extend(
        [
            "",
            "## Next step",
            "",
            "Use official provider pages to resolve flagged records. Do not promote, apply, enable billing, or invoke a provider based on this report alone.",
            "",
        ]
    )
    return "\n".join(lines)


def write_review(catalog: dict[str, Any], output: str | Path, *, today: date | None = None, stale_days: int = 90) -> dict[str, Any]:
    report = audit_catalog(catalog, today=today, stale_days=stale_days)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(report), encoding="utf-8")
    return report


def compact_catalog_for_ai(programs: Iterable[dict[str, Any]]) -> str:
    """Create a bounded catalog representation for optional AI review."""

    blocks: list[str] = []
    for p in programs:
        blocks.append(
            "\n".join(
                [
                    f"id: {p.get('id', '')}",
                    f"provider: {p.get('provider', '')}",
                    f"name: {p.get('name', '')}",
                    f"status/access: {p.get('status', '')} / {p.get('access', '')}",
                    f"benefit: {p.get('benefit', '')}",
                    f"eligibility: {', '.join(map(str, p.get('eligibility', [])))}",
                    f"requirements: {', '.join(map(str, p.get('requirements', [])))}",
                    f"evidence: {p.get('evidence_url', '')}",
                    f"last_verified: {p.get('last_verified', '')}",
                    f"handoff: {p.get('handoff', '')}",
                    f"payment_note: {p.get('payment_note', '')}",
                    f"caution: {p.get('caution', '')}",
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)
