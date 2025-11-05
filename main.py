#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
from typing import List

from tgparser.config import load_config
from tgparser.logging_setup import setup_logging
from tgparser.parser import Parser


def read_queries(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main() -> None:
    cfg = load_config()
    setup_logging(cfg)

    logger = logging.getLogger("main")

    queries = read_queries(cfg.queries_file)
    if not queries:
        logger.error("queries file is empty or missing: %s", cfg.queries_file)
        raise SystemExit(1)

    parser = Parser(cfg)
    logger.info("Starting parser...")
    parser.run(queries)


if __name__ == "__main__":
    main()
