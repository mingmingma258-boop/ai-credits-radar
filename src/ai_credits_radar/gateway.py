"""Safety-gated FREE_ONLY provider gateway."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .providers.aliyun import AliyunBailianAdapter
from .providers.base import FreeQuotaExhausted, InvocationResult, ProviderAdapter, ProviderInvocationError
from .routing import select_free_route

MAX_GLOBAL_OUTPUT_TOKENS = 2048
MAX_PROMPT_CHARS = 50000
MAX_ATTESTATION_AGE_HOURS = 24
SUPPORTED_PROVIDERS = {"aliyun-bailian"}


class GatewaySafetyError(RuntimeError):
    """A request was stopped before provider invocation by a FREE_ONLY gate."""


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resource_by_id(inventory: dict[str, Any], resource_id: str) -> dict[str, Any] | None:
    for resource in inventory.get("resources", []):
        if isinstance(resource, dict) and resource.get("id") == resource_id:
            return resource
    return None


def _adapter_for(provider_id: str, *, model: str) -> ProviderAdapter:
    if provider_id == "aliyun-bailian":
        adapter = AliyunBailianAdapter.from_env()
        adapter.model = model
        return adapter
    raise GatewaySafetyError(f"unsupported live provider: {provider_id!r}")


def live_preflight(
    inventory: dict[str, Any],
    *,
    required_tier: str = "A",
    resource_type: str = "api",
    requested_max_tokens: int = 512,
    now: datetime | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    route = select_free_route(inventory, required_tier=required_tier, resource_type=resource_type)
    if route.get("status") != "selected":
        raise GatewaySafetyError(str(route.get("reason") or "FREE_ONLY router found no safe route"))
    resource = _resource_by_id(inventory, str(route["resource_id"]))
    if resource is None:
        raise GatewaySafetyError("selected inventory resource could not be resolved")
    live = resource.get("live_use")
    if not isinstance(live, dict):
        raise GatewaySafetyError("selected resource has no live_use safety attestation")
    provider_id = live.get("provider_id")
    if provider_id not in SUPPORTED_PROVIDERS:
        raise GatewaySafetyError(f"unsupported live provider: {provider_id!r}")
    if live.get("allow_live") is not True:
        raise GatewaySafetyError("live_use.allow_live is not explicitly true")
    if live.get("free_quota_only") is not True:
        raise GatewaySafetyError("provider free-quota-only/stop protection is not confirmed")
    if live.get("paid_fallback_disabled") is not True:
        raise GatewaySafetyError("paid fallback is not explicitly confirmed disabled")
    if live.get("max_requests_per_run") != 1:
        raise GatewaySafetyError("max_requests_per_run must be exactly 1")

    configured_cap = live.get("max_output_tokens")
    if not isinstance(configured_cap, int) or isinstance(configured_cap, bool) or not 1 <= configured_cap <= MAX_GLOBAL_OUTPUT_TOKENS:
        raise GatewaySafetyError(f"live_use.max_output_tokens must be 1..{MAX_GLOBAL_OUTPUT_TOKENS}")
    if not isinstance(requested_max_tokens, int) or isinstance(requested_max_tokens, bool) or requested_max_tokens < 1:
        raise GatewaySafetyError("requested max_tokens must be a positive integer")
    effective_tokens = min(requested_max_tokens, configured_cap, MAX_GLOBAL_OUTPUT_TOKENS)

    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    confirmed = _parse_timestamp(live.get("confirmed_at"))
    synthetic_example = inventory.get("example") is True
    if not (dry_run and synthetic_example):
        if confirmed is None:
            raise GatewaySafetyError("live-use confirmation timestamp is missing or invalid")
        age_seconds = (current - confirmed).total_seconds()
        if age_seconds < -300:
            raise GatewaySafetyError("live-use confirmation timestamp is in the future")
        if age_seconds > MAX_ATTESTATION_AGE_HOURS * 3600:
            raise GatewaySafetyError("live-use confirmation is stale; re-check provider console before invoking")
    if not dry_run and synthetic_example:
        raise GatewaySafetyError("committed example inventory can never authorize a live provider request")

    return {
        "status": "preflight_ok",
        "dry_run": dry_run,
        "resource_id": route["resource_id"],
        "provider": route["provider"],
        "provider_id": provider_id,
        "model": route["model"],
        "tier": route["tier"],
        "max_output_tokens": effective_tokens,
        "billing_state": route["billing_state"],
        "quota_state": route["quota_state"],
        "free_quota_only": True,
        "paid_fallback_disabled": True,
        "max_requests_per_run": 1,
        "confirmation": "synthetic-example" if dry_run and synthetic_example else live.get("confirmed_at"),
    }


def append_usage_log(path: str | Path, event: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def invoke_free_only(
    inventory: dict[str, Any],
    *,
    prompt: str,
    required_tier: str = "A",
    resource_type: str = "api",
    max_tokens: int = 512,
    dry_run: bool = False,
    usage_log: str | Path | None = None,
    system: str | None = None,
    now: datetime | None = None,
    adapter_factory: Callable[[str, str], ProviderAdapter] | None = None,
) -> dict[str, Any]:
    if not isinstance(prompt, str) or not prompt.strip():
        raise GatewaySafetyError("prompt must be non-empty")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise GatewaySafetyError(f"prompt exceeds the {MAX_PROMPT_CHARS}-character FREE_ONLY safety cap")
    preflight = live_preflight(
        inventory,
        required_tier=required_tier,
        resource_type=resource_type,
        requested_max_tokens=max_tokens,
        now=now,
        dry_run=dry_run,
    )
    if dry_run:
        return {"status": "dry_run", "preflight": preflight, "request_sent": False}

    factory = adapter_factory or (lambda provider_id, model: _adapter_for(provider_id, model=model))
    adapter = factory(str(preflight["provider_id"]), str(preflight["model"]))
    credential = adapter.check_credentials()
    region = adapter.check_region()
    if not credential.ok:
        raise GatewaySafetyError(credential.detail)
    if not region.ok:
        raise GatewaySafetyError(region.detail)

    started = datetime.now(timezone.utc)
    try:
        result: InvocationResult = adapter.invoke(
            prompt=prompt,
            model=str(preflight["model"]),
            max_tokens=int(preflight["max_output_tokens"]),
            system=system,
            gateway_authorized=True,
        )
    except FreeQuotaExhausted as exc:
        event = {
            "time": datetime.now(timezone.utc).isoformat(),
            "status": "free_quota_exhausted",
            "provider_id": preflight["provider_id"],
            "resource_id": preflight["resource_id"],
            "model": preflight["model"],
            "request_count": 1,
        }
        if usage_log:
            append_usage_log(usage_log, event)
        raise GatewaySafetyError(str(exc)) from exc
    except ProviderInvocationError:
        raise

    event = {
        "time": datetime.now(timezone.utc).isoformat(),
        "started": started.isoformat(),
        "status": "success",
        "provider_id": preflight["provider_id"],
        "resource_id": preflight["resource_id"],
        "model": result.model,
        "usage": result.usage,
        "request_count": 1,
    }
    if usage_log:
        append_usage_log(usage_log, event)
    return {
        "status": "success",
        "preflight": preflight,
        "content": result.content,
        "model": result.model,
        "usage": result.usage,
        "request_sent": True,
    }
