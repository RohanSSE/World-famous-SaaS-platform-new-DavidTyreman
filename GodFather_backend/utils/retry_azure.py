"""Retry wrapper for Azure/OpenAI transient failures."""
from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


def with_azure_retry(
    fn: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> T:
    last_err = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            transient = any(
                x in msg
                for x in ("timeout", "429", "503", "502", "rate", "connection", "temporar")
            )
            if not transient or attempt >= max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning("Azure/OpenAI retry %s/%s: %s", attempt + 1, max_attempts, e)
            time.sleep(delay)
    raise last_err  # type: ignore[misc]
