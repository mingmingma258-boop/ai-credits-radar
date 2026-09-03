"""Credits inventory validation and summaries."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

VALID_STATUS = {"available", "rate_limited", "exhausted", "expired", "paused", "unknown"}
VALID_BILLING = {"free_tier_confirmed", "free_quota_confirmed", "unknown", "paid"}
VALID_QUOTA = {"confirmed_available", "ongoing_free_tier", "unknown", "exhausted"}
VALID_TIERS = {"Unknown", "B", "A", "S"}


def load_inventory(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"inventory not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {source}: {exc}") from exc
    errors = validate_inventory(data)
    if errors:
        raise ValueError("invalid inventory: " + "; ".join(errors))
    return data


def _iso_date(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_inventory(inventory: Any) -> list[str]:
    if not isinstance(inventory, dict):
        return ["inventory must be a JSON object"]
    resources = inventory.get("resources")
    if not isinstance(resources, list):
        return ["inventory.resources must be a list"]
    errors: list[str] = []
    seen: set[str] = set()
    for index, resource in enumerate(resources):
        prefix = f"resources[{index}]"
        if not isinstance(resource, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("id", "provider", "resource_type", "status", "free_only", "billing_state", "quota_state", "models"):
            if field not in resource:
                errors.append(f"{prefix} missing {field!r}")
        identifier = resource.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif identifier in seen:
            errors.append(f"{prefix}.id duplicated: {identifier}")
        else:
            seen.add(identifier)
        if resource.get("status") not in VALID_STATUS:
            errors.append(f"{prefix}.status must be one of {sorted(VALID_STATUS)}")
        if not isinstance(resource.get("free_only"), bool):
            errors.append(f"{prefix}.free_only must be boolean")
        if resource.get("billing_state") not in VALID_BILLING:
            errors.append(f"{prefix}.billing_state must be one of {sorted(VALID_BILLING)}")
        if resource.get("quota_state") not in VALID_QUOTA:
            errors.append(f"{prefix}.quota_state must be one of {sorted(VALID_QUOTA)}")
        remaining = resource.get("remaining")
        if remaining is not None and (not isinstance(remaining, (int, float)) or isinstance(remaining, bool) or remaining < 0):
            errors.append(f"{prefix}.remaining must be null or a non-negative number")
        if not _iso_date(resource.get("expires_at")):
            errors.append(f"{prefix}.expires_at must be null or an ISO date")
        priority = resource.get("priority", 50)
        if not isinstance(priority, int) or not 0 <= priority <= 100:
            errors.append(f"{prefix}.priority must be an integer from 0 to 100")
        models = resource.get("models")
        if not isinstance(models, list) or not models:
            errors.append(f"{prefix}.models must be a non-empty list")
        else:
            for model_index, model in enumerate(models):
                model_prefix = f"{prefix}.models[{model_index}]"
                if not isinstance(model, dict):
                    errors.append(f"{model_prefix} must be an object")
                    continue
                if not isinstance(model.get("id"), str) or not model.get("id", "").strip():
                    errors.append(f"{model_prefix}.id must be a non-empty string")
                if model.get("tier") not in VALID_TIERS:
                    errors.append(f"{model_prefix}.tier must be one of {sorted(VALID_TIERS)}")
                if not isinstance(model.get("enabled"), bool):
                    errors.append(f"{model_prefix}.enabled must be boolean")
    return errors


def inventory_summary(inventory: dict[str, Any], *, today: date | None = None, expiring_days: int = 14) -> dict[str, Any]:
    now = today or date.today()
    cutoff = now + timedelta(days=max(expiring_days, 0))
    resources = inventory.get("resources", [])
    safe_billing = {"free_tier_confirmed", "free_quota_confirmed"}
    safe_quota = {"confirmed_available", "ongoing_free_tier"}
    expiring: list[str] = []
    for resource in resources:
        expires_at = resource.get("expires_at")
        if isinstance(expires_at, str):
            try:
                expiry = date.fromisoformat(expires_at)
            except ValueError:
                continue
            if now <= expiry <= cutoff:
                expiring.append(str(resource.get("id")))
    return {
        "total": len(resources),
        "available": sum(r.get("status") == "available" for r in resources),
        "confirmed_safe_free": sum(
            r.get("free_only") is True
            and r.get("status") == "available"
            and r.get("billing_state") in safe_billing
            and r.get("quota_state") in safe_quota
            and (r.get("remaining") is None or r.get("remaining") > 0)
            for r in resources
        ),
        "unknown_billing": sum(r.get("billing_state") == "unknown" for r in resources),
        "unknown_quota": sum(r.get("quota_state") == "unknown" for r in resources),
        "expiring_soon": sorted(expiring),
    }
