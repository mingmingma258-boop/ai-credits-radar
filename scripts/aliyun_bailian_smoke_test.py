#!/usr/bin/env python3
"""Run a tiny, opt-in Alibaba Cloud Model Studio API smoke test.

The API key is read from the environment and is never printed. The script
uses only the Python standard library so it can run in GitHub Actions without
adding a project dependency.
"""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"


def main() -> int:
    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        print("DASHSCOPE_API_KEY is not set; no request was sent.", file=sys.stderr)
        return 2

    base_url = os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.environ.get("DASHSCOPE_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a connectivity smoke test. Reply with OK only."},
            {"role": "user", "content": "Reply with OK only."},
        ],
        "max_tokens": 8,
    }
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except HTTPError as exc:
        print(f"Alibaba Cloud request failed with HTTP {exc.code}; response body was withheld.", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Alibaba Cloud request could not connect: {exc.reason}", file=sys.stderr)
        return 1
    except (TimeoutError, OSError) as exc:
        print(f"Alibaba Cloud request failed: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print("Alibaba Cloud returned a non-JSON response; response body was withheld.", file=sys.stderr)
        return 1

    choices = result.get("choices") or []
    message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
    content = str(message.get("content", "")).strip().replace("\n", " ")
    usage = result.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens", "?")
    completion_tokens = usage.get("completion_tokens", "?")
    print(
        "Alibaba Cloud smoke test succeeded: "
        f"model={model}, prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}"
    )
    print(f"Model response: {content[:80] or '(empty)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
