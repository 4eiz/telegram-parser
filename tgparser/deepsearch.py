from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Set


@dataclass(frozen=True)
class DeepSearchConfig:
    enabled: bool = True
    letters: bool = True       # append ' a'..' z'
    digits: bool = True        # append ' 0'..' 9'
    min_len_gate: int = 2      # don't expand too-short queries


def generate_variants(query: str, cfg: DeepSearchConfig) -> list[str]:
    q = (query or "").strip()
    if not cfg.enabled or len(q) < cfg.min_len_gate:
        return [q] if q else []

    variants: Set[str] = set()
    variants.add(q)

    if cfg.letters:
        for ch in "abcdefghijklmnopqrstuvwxyz":
            variants.add(f"{q} {ch}")
    if cfg.digits:
        for d in "0123456789":
            variants.add(f"{q} {d}")

    # return deterministic order: base first, then sorted rest
    rest = sorted([v for v in variants if v != q])
    return [q] + rest
