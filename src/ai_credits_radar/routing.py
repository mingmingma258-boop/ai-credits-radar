"""Fail-closed free-only routing over the local credits inventory."""

from __future__ import annotations

from datetime import date
from typing import Any

from .inventory import validate_inventory

TIER_RANK = {"Unknown": 0, "B": 1, "A": 2, "S": 3}
SAFE_BILLING = {"free_tier_confirmed", "free_quota_confirmed"}
SAFE_QUOTA = {"confirmed_available", "ongoing_free_tier"}


def _expiry_key(value: Any) -> date:
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return date.max


def select_free_route(
    inventory: dict[str, Any],
    *,
    required_tier: str = "A",
    resource_type: str = "api",
    today: date | None = None,
) -> dict[str, Any]:
    """Select a confirmed-safe free route or return a hard-stop decision."""

    if required_tier not in TIER_RANK or required_tier == "Unknown":
        raise ValueError("required_tier must be B, A, or S")
    errors = validate_inventory(inventory)
    if errors:
        return {"status": "hard_stop", "reason": "invalid inventory", "errors": errors, "rejections": []}

    now = today or date.today()
    candidates: list[tuple[date, int, str, dict[str, Any], dict[str, Any]]] = []
    rejections: list[dict[str, str]] = []

    for resource in inventory.get("resources", []):
        identifier = str(resource.get("id"))
        reasons: list[str] = []
        if resource.get("resource_type") != resource_type:
            continue
        if resource.get("free_only") is not True:
            reasons.append("resource is not marked free_only")
        if resource.get("billing_state") not in SAFE_BILLING:
            reasons.append(f"billing state {resource.get('billing_state')!r} is not confirmed free")
        if resource.get("quota_state") not in SAFE_QUOTA:
            reasons.append(f"quota state {resource.get('quota_state')!r} is not confirmed usable")
        if resource.get("status") != "available":
            reasons.append(f"status is {resource.get('status')!r}, not 'available'")
        if isinstance(resource.get("remaining"), (int, float)) and resource.get("remaining") <= 0:
            reasons.append("remaining quota is zero")
        expiry = _expiry_key(resource.get("expires_at"))
        if expiry != date.max and expiry < now:
            reasons.append("resource is expired")

        eligible_models = [
            model
            for model in resource.get("models", [])
            if model.get("enabled") is True and TIER_RANK.get(str(model.get("tier")), 0) >= TIER_RANK[required_tier]
        ]
        if not eligible_models:
            reasons.append(f"no enabled model meets Tier {required_tier}")

        if reasons:
            rejections.append({"id": identifier, "reason": "; ".join(reasons)})
            continue

        model = sorted(eligible_models, key=lambda item: (TIER_RANK[str(item.get("tier"))], str(item.get("id"))))[0]
        candidates.append((expiry, -int(resource.get("priority", 50)), identifier, resource, model))

    if not candidates:
        return {
            "status": "hard_stop",
            "reason": "No confirmed-safe FREE_ONLY route satisfies the requested resource type and capability tier.",
            "required_tier": required_tier,
            "resource_type": resource_type,
            "rejections": rejections,
        }

    _, _, _, resource, model = sorted(candidates, key=lambda item: (item[0], item[1], item[2]))[0]
    return {
        "status": "selected",
        "free_only": True,
        "resource_id": resource.get("id"),
        "provider": resource.get("provider"),
        "model": model.get("id"),
        "tier": model.get("tier"),
        "billing_state": resource.get("billing_state"),
        "quota_state": resource.get("quota_state"),
        "remaining": resource.get("remaining"),
        "unit": resource.get("unit"),
        "expires_at": resource.get("expires_at"),
        "reason": "selected from confirmed-safe free resources; expiry is prioritized before configured priority",
        "rejections": rejections,
    }
