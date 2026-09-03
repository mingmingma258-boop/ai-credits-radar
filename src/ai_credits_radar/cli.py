"""Command-line interface for the AI Credits Radar catalog."""

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


def _common_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="catalog JSON path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search auditable free AI/API/GPU/cloud opportunities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list matching opportunities")
    _common_filters(list_parser)
    list_parser.add_argument("--kind", choices=["api", "cloud", "developer", "gpu", "startup", "student", "trial"])
    list_parser.add_argument("--access", choices=["account-signup", "application", "free-tier", "partner-portal", "student"])
    list_parser.add_argument("--resource", dest="resource_type", help="resource type, e.g. gpu or api")
    list_parser.add_argument("--application-only", action="store_true")
    list_parser.add_argument("--active-only", action="store_true")
    list_parser.add_argument("--json", action="store_true", dest="as_json")

    search_parser = subparsers.add_parser("search", help="search provider, benefit, eligibility, or tags")
    _common_filters(search_parser)
    search_parser.add_argument("query")
    search_parser.add_argument("--json", action="store_true", dest="as_json")

    summary_parser = subparsers.add_parser("summary", help="show catalog counts")
    _common_filters(summary_parser)

    validate_parser = subparsers.add_parser("validate", help="validate the catalog schema and links")
    _common_filters(validate_parser)
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
    print(f"{'ID':32} {'TYPE':10} {'ACCESS':18} {'MAX':>10}  NAME")
    print("-" * 100)
    for program in records:
        maximum = program.get("amount_usd_max")
        display_amount = f"${maximum:,.0f}" if maximum is not None else "—"
        print(
            f"{program['id'][:32]:32} {program['kind'][:10]:10} "
            f"{program['access'][:18]:18} {display_amount:>10}  {program['name']}"
        )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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

    if args.command == "search":
        records = filter_programs(programs, query=args.query)
        _print_records(records, args.as_json)
        return 0

    records = filter_programs(
        programs,
        kind=args.kind,
        access=args.access,
        resource_type=args.resource_type,
        application_only=args.application_only,
        active_only=args.active_only,
    )
    _print_records(records, args.as_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

