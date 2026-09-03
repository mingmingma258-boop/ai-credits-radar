"""Provider adapter contracts for future real integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderCheck:
    ok: bool
    state: str
    detail: str


class ProviderAdapter(ABC):
    """Safety-oriented provider contract.

    Implementations must not interpret unknown cost/quota state as free.
    """

    name: str

    @abstractmethod
    def check_credentials(self) -> ProviderCheck:
        raise NotImplementedError

    @abstractmethod
    def check_region(self) -> ProviderCheck:
        raise NotImplementedError

    @abstractmethod
    def check_quota(self) -> ProviderCheck:
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def estimate_cost(self, *, model: str, max_tokens: int) -> ProviderCheck:
        raise NotImplementedError

    @abstractmethod
    def invoke(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def redact_logs(self, text: str) -> str:
        raise NotImplementedError
