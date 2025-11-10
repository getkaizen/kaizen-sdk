"""Convenience decorators for wiring Kaizen into provider workflows."""

from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable, Coroutine, Optional, TypeVar

from .client import KaizenClient, KaizenClientConfig

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def with_kaizen_client(config: KaizenClientConfig | None = None) -> Callable[[F], F]:
    """Decorate an async function to auto-manage a :class:`KaizenClient` lifecycle.

    The decorated function receives a ``kaizen`` keyword argument. If the caller
    supplies one it is used; otherwise the decorator instantiates a client using
    the provided config and closes it automatically after the function returns.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            kaizen: KaizenClient | None = kwargs.get("kaizen")
            owns_client = False
            if kaizen is None:
                kaizen = KaizenClient(config=config)
                kwargs["kaizen"] = kaizen
                owns_client = True
            try:
                return await func(*args, **kwargs)
            finally:
                if owns_client:
                    await kaizen.close()

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = ["with_kaizen_client"]
