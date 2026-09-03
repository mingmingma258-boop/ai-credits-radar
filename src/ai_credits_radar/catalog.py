"""Load, validate, search, and summarize the opportunity catalog."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = ROOT / "data" / "programs.json"

REQUIRED_FIELDS = {
    "id",
    "provider",
    "name",
    "kind",
    "resource_types",
    "status",
    "access",
    "benefit",
    "amount_display",
    "eligibility",
    "requirements",
    "application_url",
    "evidence_url",
    "evidence_type",
    "last_verified",
    "priority",
    "handoff",
}
VALID_KINDS = {"api", "cloud", "developer", "gpu", "startup", "student", "trial"}
VALID_STATUS = {"active", "conditional", "verify-before-apply"}
VALID_ACCESS = {"account-signup", "application", "free-tier", "partner-portal", "student"}
VALID_HANDOFF = {"none", "login", "application-review", "verification-or-identity", "partner-code"}
VALID_SORTS = {"priority", "amount", "name", "verified"}


def load_catalog(path: str | Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    """Read a JSON catalog and fail with a useful error for malformed JSON."""

    source = Path(path)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"catalog not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {source}: {exc}") from exc


def programs_from(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    programs = catalog.get("programs")
    return programs if isinstance(programs, list) else []


def _is_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_catalog(catalog: Any) -> list[str]:
    """Return all validation errors without mutating the input."""

    errors: list[str] = []
    if not isinstance(catalog, dict):
        return ["catalog must be a JSON object"]

    programs = catalog.get("programs")
    if not isinstance(programs, list):
        return ["catalog.programs must be a list"]
    if not programs:
        errors.append("catalog.programs must not be empty")

    seen: set[str] = set()
    for index, program in enumerate(programs):
        prefix = f"programs[{index}]"
        if not isinstance(program, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - program.keys())
        errors.extend(f"{prefix} missing {field!r}" for field in missing)

        identifier = program.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif identifier in seen:
            errors.append(f"{prefix}.id is duplicated: {identifier}")
        else:
            seen.add(identifier)

        if program.get("kind") not in VALID_KINDS:
            errors.append(f"{prefix}.kind must be one of {sorted(VALID_KINDS)}")
        if program.get("status") not in VALID_STATUS:
            errors.append(f"{prefix}.status must be one of {sorted(VALID_STATUS)}")
        if program.get("access") not in VALID_ACCESS:
            errors.append(f"{prefix}.access must be one of {sorted(VALID_ACCESS)}")
        if program.get("handoff") not in VALID_HANDOFF:
            errors.append(f"{prefix}.handoff must be one of {sorted(VALID_HANDOFF)}")

        for field in ("resource_types", "eligibility", "requirements", "tags"):
            if field in program and (
                not isinstance(program[field], list)
                or not all(isinstance(item, str) and item.strip() for item in program[field])
            ):
                errors.append(f"{prefix}.{field} must be a list of non-empty strings")

        amount = program.get("amount_usd_max")
        if amount is not None and (not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount < 0):
            errors.append(f"{prefix}.amount_usd_max must be null or a non-negative number")
        if not isinstance(program.get("priority"), int) or not 0 <= program["priority"] <= 100:
            errors.append(f"{prefix}.priority must be an integer from 0 to 100")

        for field in ("application_url", "evidence_url"):
            if not _is_https_url(program.get(field)):
                errors.append(f"{prefix}.{field} must be an https URL")

        verified = program.get("last_verified")
        try:
            date.fromisoformat(verified)
        except (TypeError, ValueError):
            errors.append(f"{prefix}.last_verified must be an ISO date")

    return errors


def filter_programs(
    programs: Iterable[dict[str, Any]],
    *,
    query: str | None = None,
    kind: str | None = None,
    access: str | None = None,
    status: str | None = None,
    resource_type: str | None = None,
    application_only: bool = False,
    active_only: bool = False,
    sort_by: str = "priority",
) -> list[dict[str, Any]]:
    """Filter catalog records with case-insensitive text matching."""

    needle = (query or "").strip().casefold()
    result: list[dict[str, Any]] = []
    for program in programs:
        if kind and program.get("kind") != kind:
            continue
        if access and program.get("access") != access:
            continue
        if status and program.get("status") != status:
            continue
        if resource_type and resource_type not in program.get("resource_types", []):
            continue
        if application_only and program.get("access") != "application":
            continue
        if active_only and program.get("status") not in {"active", "conditional"}:
            continue
        if needle:
            haystack = " ".join(
                [
                    str(program.get("provider", "")),
                    str(program.get("name", "")),
                    str(program.get("benefit", "")),
                    str(program.get("eligibility", "")),
                    str(program.get("requirements", "")),
                    str(program.get("duration", "")),
                    str(program.get("notes", "")),
                    str(program.get("caution", "")),
                    str(program.get("payment_note", "")),
                    " ".join(program.get("tags", [])),
                ]
            ).casefold()
            if needle not in haystack:
                continue
        result.append(program)

    return sort_programs(result, sort_by=sort_by)


def sort_programs(programs: Iterable[dict[str, Any]], *, sort_by: str = "priority") -> list[dict[str, Any]]:
    """Return records in a predictable display order."""

    records = list(programs)
    if sort_by not in VALID_SORTS:
        sort_by = "priority"

    def common_key(item: dict[str, Any]) -> tuple[Any, ...]:
        return (
            -int(item.get("priority", 0)),
            str(item.get("provider", "")).casefold(),
            str(item.get("name", "")).casefold(),
        )

    if sort_by == "name":
        return sorted(
            records,
            key=lambda item: (
                str(item.get("name", "")).casefold(),
                str(item.get("provider", "")).casefold(),
            ),
        )
    if sort_by == "amount":
        return sorted(
            records,
            key=lambda item: (
                -(item.get("amount_usd_max") if isinstance(item.get("amount_usd_max"), (int, float)) else -1),
                *common_key(item),
            ),
        )
    if sort_by == "verified":
        return sorted(
            records,
            key=lambda item: (
                str(item.get("last_verified", "")),
                -int(item.get("priority", 0)),
                str(item.get("provider", "")).casefold(),
                str(item.get("name", "")).casefold(),
            ),
            reverse=True,
        )
    return sorted(records, key=common_key)


def summary(programs: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = list(programs)
    by_kind: dict[str, int] = {}
    by_access: dict[str, int] = {}
    for program in records:
        by_kind[program["kind"]] = by_kind.get(program["kind"], 0) + 1
        by_access[program["access"]] = by_access.get(program["access"], 0) + 1
    return {
        "total": len(records),
        "active_or_conditional": sum(program.get("status") in {"active", "conditional"} for program in records),
        "application_routes": sum(program.get("access") == "application" for program in records),
        "amounted_records": sum(program.get("amount_usd_max") is not None for program in records),
        "by_kind": dict(sorted(by_kind.items())),
        "by_access": dict(sorted(by_access.items())),
    }
