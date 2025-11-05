from __future__ import annotations

import os
from typing import Optional, Tuple
from urllib.parse import urlparse
import socks


def load_proxies(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    out: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                out.append(s)
    return out


def parse_proxy(proxy_str: str) -> Optional[Tuple[int, str, int, bool, str | None, str | None]]:
    """Return Telethon/PySocks proxy tuple:
    (ptype, host, port, rdns, username, password)
    Supports: socks5, socks4, http
    """
    try:
        s = proxy_str if "://" in proxy_str else f"socks5://{proxy_str}"
        u = urlparse(s)

        scheme = (u.scheme or "socks5").lower()
        host = u.hostname or ""
        port = int(u.port or 1080)
        username = u.username
        password = u.password

        if scheme.startswith("socks5"):
            ptype = socks.SOCKS5
        elif scheme.startswith("socks4"):
            ptype = socks.SOCKS4
        elif scheme.startswith("http"):
            ptype = socks.HTTP
        else:
            ptype = socks.SOCKS5

        return (ptype, host, port, True, username, password)
    except Exception:
        return None
