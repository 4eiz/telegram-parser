from __future__ import annotations

import random
import time
from typing import Callable


def smart_sleep(retry: int, base: float, cap: float) -> None:
    """Exponential backoff + jitter."""
    delay = min(cap, base * (2 ** retry))
    jitter = random.uniform(0.5, 1.5)
    time.sleep(delay * jitter)


def with_backoff(func: Callable, *, base: float, cap: float, retries: int = 5):
    last_exc = None
    for attempt in range(retries):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            smart_sleep(attempt, base=base, cap=cap)
    if last_exc:
        raise last_exc
