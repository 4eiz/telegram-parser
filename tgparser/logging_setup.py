from __future__ import annotations

import logging
from .config import Config


def setup_logging(cfg: Config) -> None:
    handlers = []
    stream_handler = logging.StreamHandler()
    handlers.append(stream_handler)

    if cfg.log_file:
        file_handler = logging.FileHandler(cfg.log_file, encoding="utf-8")
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, cfg.log_level, logging.INFO),
        format=cfg.log_format,
        handlers=handlers,
        force=True,
    )
