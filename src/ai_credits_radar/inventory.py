"""Credits inventory validation and summaries."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
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


def _iso_datetime(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
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

        live = resource.get("live_use")
        if live is not None:
            live_prefix = f"{prefix}.live_use"
            if not isinstance(live, dict):
                errors.append(f"{live_prefix} must be an object")
            else:
                if not isinstance(live.get("provider_id"), str) or not live.get("provider_id", "").strip():
                    errors.append(f"{live_prefix}.provider_id must be a non-empty string")
                for field in ("allow_live", "free_quota_only", "paid_fallback_disabled"):
                    if not isinstance(live.get(field), bool):
                        errors.append(f"{live_prefix}.{field} must be boolean")
                if not _iso_datetime(live.get("confirmed_at")):
                    errors.append(f"{live_prefix}.confirmed_at must be null or ISO datetime")
                max_requests = live.get("max_requests_per_run")
                if not isinstance(max_requests, int) or isinstance(max_requests, bool) or max_requests < 1:
                    errors.append(f"{live_prefix}.max_requests_per_run must be a positive integer")
                max_tokens = live.get("max_output_tokens")
                if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or not 1 <= max_tokens <= 2048:
                    errors.append(f"{live_prefix}.max_output_tokens must be an integer from 1 to 2048")
    return errors


def inventory_summary(inventory: dict[str, Any], *, today: date | None = None, expiring_days: int = 14) -> dict[str, Any]:
    now = today or date.today()
    cutoff = now + timedelta(days=max(expiring_days, 0))
    resources = inventory.get("resources", [])
    safe_billing = {"free_tier_confirmed", "free_quota_confirmed"}
    safe_quota = {"confirmed_available", "ongoing_free_tier"}
    expiring: list[str] = []
    live_ready = 0
    for resource in resources:
        expires_at = resource.get("expires_at")
        if isinstance(expires_at, str):
            try:
                expiry = date.fromisoformat(expires_at)
            except ValueError:
                continue
            if now <= expiry <= cutoff:
                expiring.append(str(resource.get("id")))
        live = resource.get("live_use")
        if (
            isinstance(live, dict)
            and live.get("allow_live") is True
            and live.get("free_quota_only") is True
            and live.get("paid_fallback_disabled") is True
        ):
            live_ready += 1
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
        "live_attested": live_ready,
        "unknown_billing": sum(r.get("billing_state") == "unknown" for r in resources),
        "unknown_quota": sum(r.get("quota_state") == "unknown" for r in resources),
        "expiring_soon": sorted(expiring),
    }
