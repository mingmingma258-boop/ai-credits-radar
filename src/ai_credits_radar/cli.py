"""Command-line interface for AI Credits Radar."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .catalog import (
    DEFAULT_DATA_PATH,
    filter_programs,
    load_catalog,
    programs_from,
    summary,
    validate_catalog,
)
from .eligibility import assess_catalog, load_profile
from .inventory import inventory_summary, load_inventory
from .review import audit_catalog, render_markdown
from .routing import select_free_route


def _common_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="catalog JSON path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search and operate an auditable free AI/API/GPU/cloud resource radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list matching opportunities")
    _common_filters(list_parser)
    list_parser.add_argument("--kind", choices=["api", "cloud", "developer", "gpu", "startup", "student", "trial"])
    list_parser.add_argument("--access", choices=["account-signup", "application", "free-tier", "partner-portal", "student"])
    list_parser.add_argument("--status", choices=["active", "conditional", "verify-before-apply"])
    list_parser.add_argument("--resource", dest="resource_type", help="resource type, e.g. gpu or api")
    list_parser.add_argument("--application-only", action="store_true")
    list_parser.add_argument("--active-only", action="store_true")
    list_parser.add_argument("--sort", choices=["priority", "amount", "name", "verified"], default="priority")
    list_parser.add_argument("--json", action="store_true", dest="as_json")

    search_parser = subparsers.add_parser("search", help="search provider, benefit, eligibility, or tags")
    _common_filters(search_parser)
    search_parser.add_argument("query")
    search_parser.add_argument("--sort", choices=["priority", "amount", "name", "verified"], default="priority")
    search_parser.add_argument("--json", action="store_true", dest="as_json")

    summary_parser = subparsers.add_parser("summary", help="show catalog counts")
    _common_filters(summary_parser)

    validate_parser = subparsers.add_parser("validate", help="validate the catalog schema and links")
    _common_filters(validate_parser)

    review_parser = subparsers.add_parser("review", help="create an offline catalog health review")
    _common_filters(review_parser)
    review_parser.add_argument("--stale-days", type=int, default=90)
    review_parser.add_argument("--output", type=Path, help="optional Markdown output path")
    review_parser.add_argument("--json", action="store_true", dest="as_json")

    eligibility_parser = subparsers.add_parser("eligibility", help="triage opportunities against a local non-sensitive profile")
    _common_filters(eligibility_parser)
    eligibility_parser.add_argument("--profile", type=Path, required=True)
    eligibility_parser.add_argument("--decision", choices=["likely", "possible", "not_match"])
    eligibility_parser.add_argument("--json", action="store_true", dest="as_json")

    inventory_parser = subparsers.add_parser("inventory", help="validate and summarize a local credits inventory")
    inventory_parser.add_argument("--inventory", type=Path, required=True)
    inventory_parser.add_argument("--json", action="store_true", dest="as_json")

    route_parser = subparsers.add_parser("route", help="choose a confirmed-safe FREE_ONLY route from a local inventory")
    route_parser.add_argument("--inventory", type=Path, required=True)
    route_parser.add_argument("--tier", choices=["B", "A", "S"], default="A")
    route_parser.add_argument("--resource", dest="resource_type", default="api")
    route_parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _load(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    catalog = load_catalog(path)
    return catalog, programs_from(catalog)


def _print_records(records: list[dict[str, Any]], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return
    if not records:
        print("No matching opportunities.")
        return
    print(f"{'ID':32} {'TYPE':10} {'STATUS':18} {'AMOUNT DISPLAY':>28}  NAME")
    print("-" * 125)
    for program in records:
        maximum = program.get("amount_usd_max")
        display_amount = str(program.get("amount_display") or (f"${maximum:,.0f}" if maximum is not None else "—"))
        print(
            f"{program['id'][:32]:32} {program['kind'][:10]:10} "
            f"{program['status'][:18]:18} {display_amount:>28}  {program['name']}"
        )


def _print_eligibility(results: list[dict[str, Any]]) -> None:
    print("NON-AUTHORITATIVE eligibility triage — confirm all provider terms manually.")
    for item in results:
        reasons = item["blockers"] or item["warnings"] or item["positives"] or ["no explicit structured signal"]
        print(f"{item['decision']:9} {item['id']}: {reasons[0]}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command in {"inventory", "route"}:
        try:
            inventory = load_inventory(args.inventory)
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if args.command == "inventory":
            result = inventory_summary(inventory)
            if args.as_json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Resources: {result['total']}")
                print(f"Available: {result['available']}")
                print(f"Confirmed safe/free: {result['confirmed_safe_free']}")
                print(f"Unknown billing: {result['unknown_billing']}")
                print(f"Unknown quota: {result['unknown_quota']}")
                print(f"Expiring soon: {', '.join(result['expiring_soon']) or 'none'}")
            return 0
        result = select_free_route(inventory, required_tier=args.tier, resource_type=args.resource_type)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result["status"] == "selected":
            print(f"FREE_ONLY route: {result['provider']} / {result['model']} (Tier {result['tier']})")
            print(f"Resource: {result['resource_id']} — expires {result.get('expires_at') or 'not specified'}")
        else:
            print(f"HARD STOP: {result['reason']}")
        return 0 if result["status"] == "selected" else 3

    try:
        catalog, programs = _load(args.data)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.command == "validate":
        errors = validate_catalog(catalog)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"Catalog valid: {len(programs)} records")
        return 0

    if args.command == "summary":
        print(json.dumps(summary(programs), ensure_ascii=False, indent=2))
        return 0

    if args.command == "review":
        report = audit_catalog(catalog, stale_days=args.stale_days)
        markdown = render_markdown(report)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(markdown, encoding="utf-8")
        if args.as_json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        elif args.output:
            print(f"Catalog review written to {args.output}")
        else:
            print(markdown)
        return 0 if not report["validation_errors"] else 1

    if args.command == "eligibility":
        try:
            profile = load_profile(args.profile)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        results = assess_catalog(programs, profile)
        if args.decision:
            results = [item for item in results if item["decision"] == args.decision]
        if args.as_json:
            print(json.dumps({"authoritative": False, "results": results}, ensure_ascii=False, indent=2))
        else:
            _print_eligibility(results)
        return 0

    if args.command == "search":
        records = filter_programs(programs, query=args.query, sort_by=args.sort)
        _print_records(records, args.as_json)
        return 0

    records = filter_programs(
        programs,
        kind=args.kind,
        access=args.access,
        status=args.status,
        resource_type=args.resource_type,
        application_only=args.application_only,
        active_only=args.active_only,
        sort_by=args.sort,
    )
    _print_records(records, args.as_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
