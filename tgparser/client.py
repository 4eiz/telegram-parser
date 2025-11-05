from __future__ import annotations

import logging
from typing import Optional, List

from telethon import TelegramClient, errors, functions, types
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import ChannelParticipantsRecent

from .proxies import parse_proxy


logger = logging.getLogger(__name__)


class TelethonWrapper:
    def __init__(self, session_path: str, api_id: int, api_hash: str, proxy_str: Optional[str] = None):
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.proxy_str = proxy_str
        self.client: Optional[TelegramClient] = None

    def _build_client(self) -> None:
        proxy = parse_proxy(self.proxy_str) if self.proxy_str else None
        logger.debug("Proxy parsed for %s: %s", self.session_path, proxy)
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash, proxy=proxy)

    def start(self) -> None:
        self._build_client()
        try:
            self.client.start()
            logger.info("Client started: %s", self.session_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to start client %s: %s", self.session_path, exc)
            raise

    def disconnect(self) -> None:
        if self.client:
            try:
                self.client.disconnect()
            except Exception:  # noqa: BLE001
                pass

    # --- Synchronous wrappers around async Telethon calls ---

    def _invoke(self, request):
        return self.client.loop.run_until_complete(self.client(request))

    def _gather_dialogs(self, limit: int):
        return self.client.loop.run_until_complete(self.client.get_dialogs(limit=limit))

    def search_public(self, query: str, limit: int = 50) -> List[types.TypeChat]:
        if not self.client:
            raise RuntimeError("Client not started")
        try:
            res = self._invoke(functions.contacts.SearchRequest(q=query, limit=limit))
            return list(res.chats)
        except errors.RPCError as exc:
            logger.warning("SearchRequest RPCError: %s. Fallback to local dialogs.", exc)
            dialogs = []
            try:
                for d in self._gather_dialogs(limit=limit):
                    if d.name and query.lower() in d.name.lower():
                        dialogs.append(d.entity)
            except Exception as ex:  # noqa: BLE001
                logger.error("get_dialogs failed: %s", ex)
            return dialogs
        except Exception as exc:  # noqa: BLE001
            logger.error("search_public unexpected error: %s", exc)
            return []

    
    def get_participants_count(self, entity) -> int | None:
        if not self.client:
            return None
        try:
            # Prefer robust count via channels.GetParticipants (recent) which returns a total .count
            if isinstance(entity, types.Channel):
                try:
                    resp = self._invoke(GetParticipantsRequest(
                        channel=entity,
                        filter=ChannelParticipantsRecent(),
                        offset=0,
                        limit=1,
                        hash=0
                    ))
                    if getattr(resp, "count", None) is not None:
                        return int(resp.count)
                except Exception as exc:  # fallback to GetFullChannelRequest
                    logger.debug("GetParticipantsRequest failed, fallback to GetFullChannelRequest: %s", exc)
                    try:
                        full = self._invoke(GetFullChannelRequest(channel=entity))
                        full_chat = getattr(full, "full_chat", None)
                        if full_chat is not None:
                            if getattr(full_chat, "participants_count", None) is not None:
                                return int(full_chat.participants_count)
                            if getattr(full_chat, "participant_count", None) is not None:
                                return int(full_chat.participant_count)
                    except Exception as exc2:
                        logger.debug("GetFullChannelRequest also failed: %s", exc2)

            if isinstance(entity, types.Chat):
                try:
                    full = self._invoke(GetFullChatRequest(chat_id=entity.id))
                    if getattr(full, "full_chat", None) and getattr(full.full_chat, "participants", None):
                        participants = getattr(full.full_chat, "participants", None)
                        try:
                            return int(getattr(participants, "count", len(getattr(participants, "participants", []))))
                        except Exception:
                            pass
                except Exception as exc:
                    logger.debug("GetFullChatRequest failed: %s", exc)

            return getattr(entity, "participants_count", None) or getattr(entity, "members_count", None)
        except errors.RPCError as exc:
            logger.warning("get_participants_count RPCError: %s", exc)
            return getattr(entity, "participants_count", None) or getattr(entity, "members_count", None)
        except Exception as exc:  # noqa: BLE001
            logger.error("get_participants_count error: %s", exc)
            return getattr(entity, "participants_count", None) or getattr(entity, "members_count", None)

    def get_link(self, entity) -> str | None:
        try:
            username = getattr(entity, "username", None)
            if username:
                return f"https://t.me/{username}"
            eid = getattr(entity, "id", None)
            if eid is not None:
                return f"id:{eid}"
            return None
        except Exception:  # noqa: BLE001
            return None
