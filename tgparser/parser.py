from __future__ import annotations

import logging
import os
import time
from typing import List

from telethon import errors, types

from .accounts import AccountManager
from .backoff import smart_sleep
from .client import TelethonWrapper
from .config import Config
from .proxies import load_proxies
from .deepsearch import DeepSearchConfig, generate_variants


logger = logging.getLogger(__name__)


class Parser:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        proxies = load_proxies(cfg.proxy_file)
        self.acc_mgr = AccountManager(cfg.accounts_dir, cfg.dead_dir, proxies)

        open(self.cfg.results_channels, "a", encoding="utf-8").close()
        open(self.cfg.results_chats, "a", encoding="utf-8").close()

    def run(self, queries: List[str]) -> None:
        # expand queries if deep search is enabled
        ds_cfg = DeepSearchConfig(
            enabled=self.cfg.deep_search_enabled,
            letters=self.cfg.deep_letters,
            digits=self.cfg.deep_digits,
            min_len_gate=self.cfg.deep_min_len_gate,
        )
        expanded_queries: list[str] = []
        for q in queries:
            expanded_queries.extend(generate_variants(q, ds_cfg))
        # dedupe keeping order
        seen = set()
        final_queries = [x for x in expanded_queries if not (x in seen or seen.add(x))]

        remaining = self.cfg.limit
        acc_idx = 0

        while self.acc_mgr.has_next() and remaining > 0:
            acc = self.acc_mgr.next_account()
            if acc is None:
                break

            proxy = self.acc_mgr.pick_proxy_for_index(acc_idx)
            acc_idx += 1

            meta = acc.meta or {}
            api_id = meta.get("app_id", None)
            api_hash = meta.get("app_hash", None)

            if api_id is None:
                api_id = self.cfg.tg_api_id
            if api_hash is None:
                api_hash = self.cfg.tg_api_hash

            try:
                api_id = int(api_id) if api_id is not None else None
            except Exception:  # noqa: BLE001
                api_id = None

            if not api_id or not api_hash:
                logger.error("Missing api_id/api_hash for %s. Skipping.", acc.json_path or acc.session_path)
                continue

            wrapper = TelethonWrapper(
                session_path=acc.session_path,
                api_id=api_id,
                api_hash=str(api_hash),
                proxy_str=proxy,
            )

            started = False
            for attempt in range(5):
                try:
                    wrapper.start()
                    started = True
                    break
                except Exception as exc:  # noqa: BLE001
                    logger.error("Start failed: %s (attempt %d)", exc, attempt)
                    smart_sleep(attempt, base=self.cfg.base_backoff, cap=self.cfg.backoff_cap)

            if not started:
                logger.error("Could not start account. Marking dead.")
                self.acc_mgr.mark_dead(acc)
                continue

            try:
                for query in final_queries:
                    if remaining <= 0:
                        break

                    per_call = min(20, remaining)
                    logger.info("Searching '%s' (limit %d)", query, per_call)

                    results = None
                    for attempt in range(6):
                        try:
                            results = wrapper.search_public(query, limit=per_call)
                            break
                        except errors.FloodWaitError as e:
                            logger.warning("FloodWait: sleeping %ds", e.seconds)
                            time.sleep(e.seconds + 1)
                        except Exception as exc:  # noqa: BLE001
                            logger.error("Search error: %s (attempt %d)", exc, attempt)
                            smart_sleep(attempt, base=self.cfg.base_backoff, cap=self.cfg.backoff_cap)

                    if results is None:
                        results = []

                    for ent in results:
                        if remaining <= 0:
                            break

                        is_channel = isinstance(ent, types.Channel) and bool(getattr(ent, "broadcast", False))
                        is_chat = isinstance(ent, types.Chat) or (isinstance(ent, types.Channel) and bool(getattr(ent, "megagroup", False)))

                        if self.cfg.search_type == "channel" and not is_channel:
                            continue
                        if self.cfg.search_type == "chat" and not is_chat:
                            continue

                        title = getattr(ent, "title", None) or getattr(ent, "name", None) or "NO_TITLE"
                        count = wrapper.get_participants_count(ent) or 0
                        link = wrapper.get_link(ent) or "NO_LINK"

                        line = f"{title} | {count} | {link}"
                        target_file = self.cfg.results_channels if is_channel else self.cfg.results_chats
                        with open(target_file, "a", encoding="utf-8") as f:
                            f.write(line + "\n")

                        remaining -= 1

                    smart_sleep(0, base=self.cfg.base_backoff, cap=self.cfg.backoff_cap)

            except (errors.SessionPasswordNeededError, errors.AuthKeyError, errors.PhoneNumberInvalidError) as exc:
                logger.error("Critical account error: %s. Moving to dead.", exc)
                try:
                    wrapper.disconnect()
                except Exception:  # noqa: BLE001
                    pass
                self.acc_mgr.mark_dead(acc)
                continue
            except Exception as exc:  # noqa: BLE001
                logger.exception("Unhandled error with account: %s", exc)
                try:
                    wrapper.disconnect()
                except Exception:  # noqa: BLE001
                    pass
                continue

            try:
                wrapper.disconnect()
            except Exception:  # noqa: BLE001
                pass

        logger.info("Finished. Results saved to '%s' and '%s'.", self.cfg.results_channels, self.cfg.results_chats)
