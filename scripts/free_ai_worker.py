#!/usr/bin/env python3
"""Run the bounded FREE_ONLY worker locally or from a manual Actions attestation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ai_credits_radar.gateway import GatewaySafetyError
from ai_credits_radar.inventory import load_inventory
from ai_credits_radar.providers.base import ProviderInvocationError
from ai_credits_radar.worker import load_worker_task, run_worker

ROOT = Path(__file__).resolve().parents[1]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run bounded AI Credits Radar FREE_ONLY worker")
    result.add_argument("--task", type=Path)
    result.add_argument("--inventory", type=Path)
    result.add_argument("--repo-root", type=Path, default=ROOT)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--usage-log", type=Path)
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--actions-env", action="store_true", help="build ephemeral task/inventory from WORKER_* environment variables")
    return result


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().casefold() in {"1", "true", "yes", "on"}


def _actions_state() -> tuple[dict[str, object], dict[str, object]]:
    goal = os.environ.get("WORKER_TASK_TEXT", "").strip()
    if not goal:
        raise ValueError("WORKER_TASK_TEXT is required")
    contexts = [item.strip() for item in os.environ.get("WORKER_CONTEXT_FILES", "").split(",") if item.strip()]
    model = os.environ.get("WORKER_MODEL", "qwen-plus").strip() or "qwen-plus"
    tier = os.environ.get("WORKER_MODEL_TIER", "A").strip() or "A"
    max_tokens = int(os.environ.get("WORKER_MAX_OUTPUT_TOKENS", "800"))
    thinking_mode = os.environ.get("WORKER_THINKING_MODE", "fast").strip().casefold() or "fast"
    thinking_budget_raw = os.environ.get("WORKER_THINKING_BUDGET", "").strip()
    thinking_budget = int(thinking_budget_raw) if thinking_mode == "reasoning" and thinking_budget_raw else None
    confirmed_free = _bool_env("WORKER_FREE_QUOTA_CONFIRMED")
    stop_confirmed = _bool_env("WORKER_FREE_QUOTA_ONLY_CONFIRMED")
    expires_at = os.environ.get("WORKER_QUOTA_EXPIRES_AT", "").strip() or None
    now = datetime.now(timezone.utc).isoformat()
    task: dict[str, object] = {
        "project": "P001",
        "task_id": "ACTIONS-MANUAL",
        "goal": goal,
        "instructions": "Produce reviewable artifacts only; do not claim repository writes or command execution.",
        "context_files": contexts,
        "tier": tier,
        "max_output_tokens": max_tokens,
        "thinking_mode": thinking_mode,
        "thinking_budget": thinking_budget,
    }
    inventory: dict[str, object] = {
        "schema_version": 1,
        "example": False,
        "resources": [
            {
                "id": "actions-aliyun-free-quota",
                "provider": "Alibaba Cloud Model Studio",
                "resource_type": "api",
                "status": "available" if confirmed_free else "unknown",
                "free_only": confirmed_free,
                "billing_state": "free_quota_confirmed" if confirmed_free else "unknown",
                "quota_state": "confirmed_available" if confirmed_free else "unknown",
                "remaining": None,
                "unit": "tokens",
                "expires_at": expires_at,
                "priority": 100,
                "models": [{"id": model, "tier": tier, "enabled": True}],
                "live_use": {
                    "provider_id": "aliyun-bailian",
                    "allow_live": confirmed_free and stop_confirmed,
                    "free_quota_only": stop_confirmed,
                    "paid_fallback_disabled": stop_confirmed,
                    "confirmed_at": now if confirmed_free and stop_confirmed else None,
                    "max_requests_per_run": 1,
                    "max_output_tokens": max_tokens,
                },
            }
        ],
    }
    return task, inventory


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.actions_env:
            task, inventory = _actions_state()
        else:
            if not args.task or not args.inventory:
                raise ValueError("--task and --inventory are required unless --actions-env is used")
            task = load_worker_task(args.task)
            inventory = load_inventory(args.inventory)
        metadata = run_worker(
            task,
            inventory,
            repo_root=args.repo_root,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
            usage_log=args.usage_log,
        )
    except (FileNotFoundError, ValueError, GatewaySafetyError) as exc:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "hard-stop.json").write_text(
            json.dumps({"status": "hard_stop", "reason": str(exc)}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"HARD STOP: {exc}", file=sys.stderr)
        return 0 if args.dry_run else 3
    except ProviderInvocationError as exc:
        # run_worker has already written sanitized run/failure artifacts.
        print(f"PROVIDER ERROR: {exc}", file=sys.stderr)
        return 4
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
