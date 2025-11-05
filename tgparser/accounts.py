from __future__ import annotations

import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from typing import Optional, List


logger = logging.getLogger(__name__)


@dataclass
class AccountMeta:
    session_path: str
    json_path: Optional[str] = None
    meta: dict = field(default_factory=dict)


class AccountManager:
    def __init__(self, accounts_dir: str, dead_dir: str, proxies: List[str] | None = None):
        self.accounts_dir = accounts_dir
        self.dead_dir = dead_dir
        self.proxies = proxies or []
        self._accounts: list[AccountMeta] = self._discover_accounts()
        self._index = 0

    def _discover_accounts(self) -> list[AccountMeta]:
        result: list[AccountMeta] = []
        if not os.path.exists(self.accounts_dir):
            logger.warning("Accounts dir does not exist: %s", self.accounts_dir)
            return result

        for fname in sorted(os.listdir(self.accounts_dir)):
            full = os.path.join(self.accounts_dir, fname)
            if fname == "dead":
                continue
            if not fname.lower().endswith(".json"):
                continue

            try:
                with open(full, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to load account JSON %s: %s", full, exc)
                meta = {}

            session_file = meta.get("session_file")
            if not session_file:
                base = os.path.splitext(os.path.basename(full))[0]
                cand1 = os.path.join(self.accounts_dir, f"{base}_telethon.session")
                cand2 = os.path.join(self.accounts_dir, f"{base}.session")
                session_full = cand1 if os.path.exists(cand1) else cand2
            else:
                session_full = session_file if os.path.isabs(session_file) else os.path.join(self.accounts_dir, os.path.basename(session_file))

            acc = AccountMeta(session_path=session_full, json_path=full, meta=meta)
            result.append(acc)

        logger.info("Discovered %d accounts", len(result))
        return result

    def has_next(self) -> bool:
        return self._index < len(self._accounts)

    def next_account(self) -> Optional[AccountMeta]:
        if not self.has_next():
            return None
        acc = self._accounts[self._index]
        self._index += 1
        return acc

    def pick_proxy_for_index(self, idx: int) -> Optional[str]:
        if not self.proxies:
            return None
        return self.proxies[idx % len(self.proxies)]

    def mark_dead(self, acc: AccountMeta) -> None:
        os.makedirs(self.dead_dir, exist_ok=True)
        try:
            if os.path.exists(acc.session_path):
                shutil.move(acc.session_path, os.path.join(self.dead_dir, os.path.basename(acc.session_path)))
            if acc.json_path and os.path.exists(acc.json_path):
                shutil.move(acc.json_path, os.path.join(self.dead_dir, os.path.basename(acc.json_path)))
            logger.warning("Account moved to dead: %s", acc.json_path or acc.session_path)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to move account to dead: %s", exc)
