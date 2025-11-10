"""Core Kaizen HTTP client used by SDK integrations."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, MutableMapping, Optional, Type, TypeVar, Union

import httpx
from pydantic import BaseModel

from .exceptions import KaizenAPIError, KaizenRequestError
from .models import (
    DecodeRequest,
    EncodeRequest,
    OptimizeRequestPayload,
    OptimizeResponsePayload,
    PromptDecodePayload,
    PromptEncodePayload,
)

DEFAULT_BASE_URL = os.getenv("KAIZEN_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_TIMEOUT = float(os.getenv("KAIZEN_TIMEOUT", "30"))
DEFAULT_API_KEY = os.getenv("KAIZEN_API_KEY")

ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(slots=True)
class KaizenClientConfig:
    """Runtime configuration for the SDK."""

    base_url: str = DEFAULT_BASE_URL
    api_key: Optional[str] = DEFAULT_API_KEY
    timeout: float = DEFAULT_TIMEOUT
    verify_ssl: bool = True
    default_headers: Dict[str, str] = field(default_factory=dict)


class KaizenClient:
    """Production-grade async client for the Kaizen HTTP API."""

    def __init__(
        self,
        config: KaizenClientConfig | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config or KaizenClientConfig()
        self._base_url = self._config.base_url.rstrip("/")
        if client is None:
            self._client = httpx.AsyncClient(
                timeout=self._config.timeout,
                base_url=self._base_url,
                verify=self._config.verify_ssl,
            )
            self._owns_client = True
        else:
            self._client = client
            self._owns_client = False

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "KaizenClient":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # High-level API surface
    # ------------------------------------------------------------------
    async def compress(self, payload: EncodeRequest | Mapping[str, Any]) -> Dict[str, Any]:
        return await self._post("v1/compress", payload, request_model=EncodeRequest)

    async def decompress(self, payload: DecodeRequest | Mapping[str, Any]) -> Dict[str, Any]:
        return await self._post("v1/decompress", payload, request_model=DecodeRequest)

    async def optimize(self, payload: EncodeRequest | Mapping[str, Any]) -> Dict[str, Any]:
        return await self._post("v1/optimize", payload, request_model=EncodeRequest)

    async def optimize_request(self, payload: OptimizeRequestPayload | Mapping[str, Any]) -> Dict[str, Any]:
        return await self._post("v1/optimize/request", payload, request_model=OptimizeRequestPayload)

    async def optimize_response(self, payload: OptimizeResponsePayload | Mapping[str, Any]) -> Dict[str, Any]:
        return await self._post("v1/optimize/response", payload, request_model=OptimizeResponsePayload)

    async def prompts_encode(
        self,
        payload: PromptEncodePayload | Mapping[str, Any],
    ) -> Dict[str, Any]:
        return await self._post("v1/prompts/encode", payload, request_model=PromptEncodePayload)

    async def prompts_decode(
        self,
        payload: PromptDecodePayload | Mapping[str, Any],
    ) -> Dict[str, Any]:
        return await self._post("v1/prompts/decode", payload, request_model=PromptDecodePayload)

    async def health(self) -> Dict[str, Any]:
        return await self._request("GET", "/")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _post(
        self,
        path: str,
        payload: Mapping[str, Any] | BaseModel,
        *,
        request_model: Type[ModelT] | None = None,
        response_model: Type[ModelT] | None = None,
    ) -> Union[Dict[str, Any], ModelT]:
        json_payload = self._normalize_payload(payload, request_model)
        data = await self._request("POST", path, json_payload)
        if response_model is not None:
            return response_model.model_validate(data)
        return data

    async def _request(
        self,
        method: str,
        path: str,
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self._resolve_path(path)
        headers = self._build_headers()
        try:
            response = await self._client.request(method, url, json=json_payload, headers=headers)
        except httpx.HTTPError as exc:  # pragma: no cover - network errors in tests
            raise KaizenRequestError("Failed to reach Kaizen API", exc) from exc

        if response.is_error:
            payload: Any
            try:
                payload = response.json()
            except ValueError:  # pragma: no cover - rarely hit
                payload = response.text
            raise KaizenAPIError(response.status_code, payload, response.headers)

        try:
            return response.json()
        except ValueError as exc:
            raise KaizenAPIError(response.status_code, "Malformed JSON response", response.headers) from exc

    def _normalize_payload(
        self,
        payload: Mapping[str, Any] | BaseModel,
        model_cls: Optional[Type[ModelT]],
    ) -> Dict[str, Any]:
        if isinstance(payload, BaseModel):
            return payload.model_dump(exclude_none=True)
        if model_cls is not None:
            return model_cls.model_validate(dict(payload)).model_dump(exclude_none=True)
        return dict(payload)

    def _build_headers(self) -> Dict[str, str]:
        headers = dict(self._config.default_headers)
        headers.setdefault("Content-Type", "application/json")
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        return headers

    def _resolve_path(self, path: str) -> str:
        clean = path if path.startswith("http") else f"{self._base_url}/{path.lstrip('/')}"
        return clean

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------
    @classmethod
    def from_env(cls) -> "KaizenClient":
        return cls(KaizenClientConfig())


__all__ = ["KaizenClient", "KaizenClientConfig", "DEFAULT_BASE_URL"]
