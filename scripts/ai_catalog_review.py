#!/usr/bin/env python3
"""Generate a catalog-review artifact; AI invocation is explicit and opt-in."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_credits_radar.catalog import DEFAULT_DATA_PATH, load_catalog, programs_from, validate_catalog
from ai_credits_radar.review import audit_catalog, compact_catalog_for_ai, render_markdown

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an AI Credits Radar catalog review artifact")
    parser.add_argument("--mode", choices=["dry-run", "invoke"], default="dry-run")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default=os.environ.get("DASHSCOPE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--max-tokens", type=int, default=int(os.environ.get("AI_REVIEW_MAX_TOKENS", "900")))
    return parser


def _invoke(*, prompt: str, model: str, max_tokens: int) -> tuple[str, dict[str, object]]:
    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not set; no request was sent.")
    base_url = os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    bounded_tokens = max(1, min(max_tokens, 1500))
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You review only the supplied AI Credits Radar catalog. Do not browse, invent provider facts, "
                    "claim current eligibility, or recommend bypassing provider controls. Return concise Markdown. "
                    "Flag ambiguity as needs-verification. Focus on inconsistent wording, missing/weak eligibility or "
                    "billing warnings, stale-looking claims, and records that require human takeover. Do not output secrets."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": bounded_tokens,
        "temperature": 0.2,
    }
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"AI catalog review failed with HTTP {exc.code}; response body withheld.") from exc
    except URLError as exc:
        raise RuntimeError(f"AI catalog review could not connect: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise RuntimeError(f"AI catalog review request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("AI catalog review returned non-JSON; response body withheld.") from exc

    choices = result.get("choices") or []
    message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
    content = str(message.get("content", "")).strip()
    if not content:
        raise RuntimeError("AI catalog review returned no review content.")
    usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
    return content, usage


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        catalog = load_catalog(args.data)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    errors = validate_catalog(catalog)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    offline = audit_catalog(catalog)
    body = [render_markdown(offline), "", "---", "", "# Optional AI Review", ""]
    if args.mode == "dry-run":
        body.extend(
            [
                "Mode: **dry-run** — no provider request was sent.",
                "",
                f"Prepared {len(programs_from(catalog))} catalog records for an optional bounded AI review.",
                "Run the manual GitHub workflow in `invoke` mode only after confirming free quota and model/billing safety in the provider console.",
            ]
        )
    else:
        prompt = (
            "Review the following catalog records. Use only these supplied fields and the offline-audit context. "
            "Return sections: High priority review, Eligibility/region ambiguity, Billing/free-only risks, Human handoff, "
            "and Suggested manual verification. Do not propose automatic catalog edits.\n\n"
            + compact_catalog_for_ai(programs_from(catalog))
        )
        try:
            ai_review, usage = _invoke(prompt=prompt, model=args.model, max_tokens=args.max_tokens)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        body.extend(
            [
                f"Mode: **invoke**; model: `{args.model}`; output is advisory and must be human-reviewed.",
                "",
                ai_review,
                "",
                "## Usage metadata",
                "",
                f"- prompt_tokens: {usage.get('prompt_tokens', '?')}",
                f"- completion_tokens: {usage.get('completion_tokens', '?')}",
            ]
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"Catalog review artifact written to {args.output}; mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
