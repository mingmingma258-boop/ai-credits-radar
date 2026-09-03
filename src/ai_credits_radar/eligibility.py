"""Transparent, non-authoritative eligibility triage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

ALLOWED_PROFILE_FIELDS = {
    "region",
    "student",
    "independent_developer",
    "startup",
    "researcher",
    "has_student_email",
    "has_github",
    "allow_payment_method",
    "accept_identity_verification",
}


def load_profile(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    profile = data.get("profile") if isinstance(data, dict) and "profile" in data else data
    if not isinstance(profile, dict):
        raise ValueError("profile must be a JSON object or a top-level 'profile' object")
    errors = validate_profile(profile)
    if errors:
        raise ValueError("invalid profile: " + "; ".join(errors))
    return profile


def validate_profile(profile: Any) -> list[str]:
    if not isinstance(profile, dict):
        return ["profile must be an object"]
    errors: list[str] = []
    unknown = sorted(set(profile) - ALLOWED_PROFILE_FIELDS)
    if unknown:
        errors.append("unsupported profile fields: " + ", ".join(unknown))
    if not isinstance(profile.get("region"), str) or not profile.get("region", "").strip():
        errors.append("region must be a non-empty string")
    for field in ALLOWED_PROFILE_FIELDS - {"region"}:
        if field in profile and not isinstance(profile[field], bool):
            errors.append(f"{field} must be boolean")
    return errors


def _text(program: dict[str, Any]) -> str:
    values: list[str] = [
        str(program.get("kind", "")),
        str(program.get("access", "")),
        str(program.get("provider", "")),
    ]
    for field in ("eligibility", "requirements", "tags"):
        value = program.get(field, [])
        if isinstance(value, list):
            values.extend(str(item) for item in value)
    values.extend([str(program.get("payment_note", "")), str(program.get("caution", ""))])
    return " ".join(values).casefold()


def assess_program(program: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Triage one program without claiming official/provider eligibility."""

    text = _text(program)
    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    if program.get("kind") == "startup" and not profile.get("startup", False):
        blockers.append("program is startup-focused but profile.startup is false")
    if (program.get("kind") == "student" or program.get("access") == "student") and not profile.get("student", False):
        blockers.append("program requires student status but profile.student is false")
    if "academic email" in text or "school email" in text or "student email" in text:
        if not profile.get("has_student_email", False):
            blockers.append("program appears to require an academic/student email")
        else:
            positives.append("profile has a student email; provider verification is still required")
    if "github" in text:
        if not profile.get("has_github", False):
            blockers.append("program appears to require GitHub")
        else:
            positives.append("profile indicates GitHub is available")
    if "developer" in text and profile.get("independent_developer", False):
        positives.append("developer-oriented requirements align with the profile")
    if "research" in text and profile.get("researcher", False):
        positives.append("research-oriented language aligns with the profile")

    if any(token in text for token in ("credit card", "payment method", "billing verification", "payment verification")):
        if not profile.get("allow_payment_method", False):
            warnings.append("payment/card verification may be requested and profile disallows payment-method steps")
    if program.get("handoff") in {"verification-or-identity", "application-review", "login", "partner-code"}:
        warnings.append(f"human takeover expected: {program.get('handoff')}")
    if program.get("handoff") == "verification-or-identity" and not profile.get("accept_identity_verification", False):
        warnings.append("identity/student verification may be required but profile does not pre-approve it")
    if program.get("status") in {"conditional", "verify-before-apply"}:
        warnings.append(f"catalog status is {program.get('status')}; current official terms need confirmation")
    if "eligible region" in text or "region" in text:
        warnings.append(f"region must be confirmed by the provider for profile region {profile.get('region')}")

    if blockers:
        decision = "not_match"
    elif warnings:
        decision = "possible"
    else:
        decision = "likely"

    return {
        "id": program.get("id"),
        "provider": program.get("provider"),
        "name": program.get("name"),
        "decision": decision,
        "authoritative": False,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "application_url": program.get("application_url"),
        "evidence_url": program.get("evidence_url"),
    }


def assess_catalog(programs: Iterable[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    order = {"likely": 0, "possible": 1, "not_match": 2}
    results = [assess_program(program, profile) for program in programs]
    return sorted(results, key=lambda item: (order[item["decision"]], str(item.get("provider", "")), str(item.get("name", ""))))
