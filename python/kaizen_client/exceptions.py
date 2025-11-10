"""Custom exception hierarchy for the Kaizen SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional


class KaizenError(Exception):
    """Base exception for all SDK errors."""


@dataclass(slots=True)
class KaizenRequestError(KaizenError):
    """Raised when the HTTP request fails before reaching the API."""

    message: str
    original: Exception | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


@dataclass(slots=True)
class KaizenAPIError(KaizenError):
    """Raised when the Kaizen API returns an error status code."""

    status_code: int
    payload: Any
    headers: Mapping[str, str] | MutableMapping[str, str]

    def __str__(self) -> str:
        return f"Kaizen API error ({self.status_code}): {self.payload!r}"


__all__ = ["KaizenError", "KaizenRequestError", "KaizenAPIError"]
