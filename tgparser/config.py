from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    tg_api_id: int | None
    tg_api_hash: str | None

    search_type: str
    limit: int

    accounts_dir: str
    dead_dir: str
    proxy_file: str
    queries_file: str

    results_channels: str
    results_chats: str

    log_level: str
    log_file: str | None
    log_format: str

    base_backoff: float
    backoff_cap: float

    deep_search_enabled: bool
    deep_letters: bool
    deep_digits: bool
    deep_min_len_gate: int


def load_config() -> Config:
    load_dotenv()

    tg_api_id_raw = os.getenv("TG_API_ID")
    tg_api_id = int(tg_api_id_raw) if tg_api_id_raw and tg_api_id_raw.isdigit() else None
    tg_api_hash = os.getenv("TG_API_HASH")

    search_type = os.getenv("SEARCH_TYPE", "all").lower()
    limit = int(os.getenv("LIMIT", "50"))

    accounts_dir = os.getenv("ACCOUNTS_DIR", "Accounts")
    dead_dir = os.getenv("DEAD_DIR", os.path.join(accounts_dir, "dead"))
    proxy_file = os.getenv("PROXY_FILE", "proxy.txt")
    queries_file = os.getenv("QUERIES_FILE", "queries.txt")

    results_channels = os.getenv("RESULTS_CHANNELS", "results_channels.txt")
    results_chats = os.getenv("RESULTS_CHATS", "results_chats.txt")

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE")
    log_format = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    base_backoff = float(os.getenv("BASE_BACKOFF", "1.0"))
    backoff_cap = float(os.getenv("BACKOFF_CAP", "60.0"))

    deep_search_enabled = os.getenv("DEEP_SEARCH", "1") not in ("0", "false", "False")
    deep_letters = os.getenv("DEEP_LETTERS", "1") not in ("0", "false", "False")
    deep_digits = os.getenv("DEEP_DIGITS", "1") not in ("0", "false", "False")
    deep_min_len_gate = int(os.getenv("DEEP_MIN_LEN", "2"))

    return Config(
        tg_api_id=tg_api_id,
        tg_api_hash=tg_api_hash,
        search_type=search_type,
        limit=limit,
        accounts_dir=accounts_dir,
        dead_dir=dead_dir,
        proxy_file=proxy_file,
        queries_file=queries_file,
        results_channels=results_channels,
        results_chats=results_chats,
        log_level=log_level,
        log_file=log_file,
        log_format=log_format,
        base_backoff=base_backoff,
        backoff_cap=backoff_cap,
        deep_search_enabled=deep_search_enabled,
        deep_letters=deep_letters,
        deep_digits=deep_digits,
        deep_min_len_gate=deep_min_len_gate,
    )
