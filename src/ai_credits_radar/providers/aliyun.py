"""Alibaba Cloud Model Studio adapter.

The adapter performs exactly one OpenAI-compatible request when invoked. It
never decides that a call is free by itself; the FREE_ONLY gateway must make
that decision from explicit inventory/attestation state before calling it.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import FreeQuotaExhausted, InvocationResult, ProviderAdapter, ProviderCheck, ProviderInvocationError

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"
MAX_OUTPUT_TOKENS = 2048


class AliyunBailianAdapter(ProviderAdapter):
    name = "Alibaba Cloud Model Studio"
    provider_id = "aliyun-bailian"

    def __init__(self, *, api_key: str = "", base_url: str = DEFAULT_BASE_URL, model: str = DEFAULT_MODEL):
        self._api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip() or DEFAULT_MODEL

    @classmethod
    def from_env(cls) -> "AliyunBailianAdapter":
        return cls(
            api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
            base_url=os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL),
            model=os.environ.get("DASHSCOPE_MODEL", DEFAULT_MODEL),
        )

    def check_credentials(self) -> ProviderCheck:
        if self._api_key:
            return ProviderCheck(True, "configured", "DASHSCOPE_API_KEY is present; value is not displayed.")
        return ProviderCheck(False, "missing", "DASHSCOPE_API_KEY is not configured; no request can be sent.")

    def check_region(self) -> ProviderCheck:
        if not self.base_url.startswith("https://"):
            return ProviderCheck(False, "invalid", "Base URL must use HTTPS.")
        return ProviderCheck(True, "configured", f"Base URL configured: {self.base_url}")

    def check_quota(self) -> ProviderCheck:
        return ProviderCheck(
            False,
            "unknown",
            "The adapter cannot prove remaining free quota. FREE_ONLY gateway attestation is required before invocation.",
        )

    def list_models(self) -> list[dict[str, Any]]:
        return [{"id": self.model, "tier": "Unknown", "source": "local configuration"}]

    def estimate_cost(self, *, model: str, max_tokens: int) -> ProviderCheck:
        return ProviderCheck(
            False,
            "unknown",
            f"Cost/free-quota status for model={model!r}, max_tokens={max_tokens} is not inferred by the adapter.",
        )

    @staticmethod
    def _error_code(body: bytes) -> str | None:
        try:
            payload = json.loads(body.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        direct = payload.get("code")
        if isinstance(direct, str):
            return direct
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            return error["code"]
        return None

    def invoke(
        self,
        *,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 512,
        system: str | None = None,
        timeout: int = 45,
    ) -> InvocationResult:
        credential = self.check_credentials()
        region = self.check_region()
        if not credential.ok:
            raise ProviderInvocationError(credential.detail)
        if not region.ok:
            raise ProviderInvocationError(region.detail)
        bounded_tokens = max(1, min(int(max_tokens), MAX_OUTPUT_TOKENS))
        selected_model = (model or self.model).strip() or self.model
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": selected_model,
            "messages": messages,
            "max_tokens": bounded_tokens,
            "temperature": 0.2,
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=max(1, min(int(timeout), 60))) as response:
                result = json.load(response)
                request_id = response.headers.get("x-request-id")
        except HTTPError as exc:
            body = exc.read(32768)
            code = self._error_code(body)
            if exc.code == 403 and code == "AllocationQuota.FreeTierOnly":
                raise FreeQuotaExhausted(
                    "Alibaba FREE_ONLY quota is exhausted; provider stopped the request before paid fallback."
                ) from exc
            raise ProviderInvocationError(f"Alibaba request failed with HTTP {exc.code}; response body withheld.") from exc
        except URLError as exc:
            raise ProviderInvocationError(f"Alibaba request could not connect: {exc.reason}") from exc
        except (TimeoutError, OSError) as exc:
            raise ProviderInvocationError(f"Alibaba request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ProviderInvocationError("Alibaba returned non-JSON; response body withheld.") from exc

        choices = result.get("choices") or []
        message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
        content = str(message.get("content", "")).strip()
        if not content:
            raise ProviderInvocationError("Alibaba returned no model content.")
        usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
        return InvocationResult(content=content, model=selected_model, usage=dict(usage), provider_request_id=request_id)

    def redact_logs(self, text: str) -> str:
        if self._api_key:
            return text.replace(self._api_key, "[REDACTED]")
        return text
