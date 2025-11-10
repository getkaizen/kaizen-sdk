"""Typed request/response models generated from the Kaizen OpenAPI schema."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class _BaseModel(BaseModel):
    """Common BaseModel config."""

    model_config = {"extra": "forbid", "populate_by_name": True}


class EncodeOptions(_BaseModel):
    delimiter: Optional[str] = Field(default=None, min_length=1, max_length=1)
    indent: Optional[int] = Field(default=None, ge=1)
    length_marker: Optional[Union[bool, str]] = None


class DecodeOptions(_BaseModel):
    indent: Optional[int] = Field(default=None, ge=1)
    strict: Optional[bool] = Field(default=True)


class EncodeRequest(_BaseModel):
    data: Any
    options: Optional[EncodeOptions] = None


class DecodeRequest(_BaseModel):
    data: str
    options: Optional[DecodeOptions] = None


class PromptEncodePayload(_BaseModel):
    prompt: Any
    options: Optional[EncodeOptions] = None
    auto_detect_json: bool = True
    schemas: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    token_models: Optional[List[str]] = None


class PromptDecodePayload(_BaseModel):
    ktof: str
    options: Optional[DecodeOptions] = None
    replay_meta: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class OptimizeRequestPayload(_BaseModel):
    prompt: Any
    options: Optional[EncodeOptions] = None
    auto_detect_json: bool = True
    metadata: Optional[Dict[str, Any]] = None
    token_models: Optional[List[str]] = None


class OptimizeResponsePayload(_BaseModel):
    ktof: str
    options: Optional[DecodeOptions] = None


__all__ = [
    "EncodeOptions",
    "DecodeOptions",
    "EncodeRequest",
    "DecodeRequest",
    "PromptEncodePayload",
    "PromptDecodePayload",
    "OptimizeRequestPayload",
    "OptimizeResponsePayload",
]
