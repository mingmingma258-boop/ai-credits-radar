"""Offline configuration adapter for Alibaba Cloud Model Studio.

Live invocation intentionally remains in the existing manually triggered smoke-test path.
"""

from __future__ import annotations

import os
from typing import Any

from .base import ProviderAdapter, ProviderCheck

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"


class AliyunBailianAdapter(ProviderAdapter):
    name = "Alibaba Cloud Model Studio"

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
            "Quota is not checked offline. Confirm free quota and auto-stop in the provider console before invocation.",
        )

    def list_models(self) -> list[dict[str, Any]]:
        return [{"id": self.model, "tier": "Unknown", "source": "local configuration"}]

    def estimate_cost(self, *, model: str, max_tokens: int) -> ProviderCheck:
        return ProviderCheck(
            False,
            "unknown",
            f"Cost/free-quota status for model={model!r}, max_tokens={max_tokens} is unknown offline; do not assume free.",
        )

    def invoke(self, **kwargs: Any) -> Any:
        raise RuntimeError(
            "Live invocation is intentionally disabled in the prototype adapter. Use the explicitly manual smoke-test or AI-review workflow after confirming free quota."
        )

    def redact_logs(self, text: str) -> str:
        if self._api_key:
            return text.replace(self._api_key, "[REDACTED]")
        return text
