from __future__ import annotations

import logging
import sys

from config.env_config import AppConfig

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(config: AppConfig) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(config.log_level)

    formatter = logging.Formatter(_LOG_FORMAT)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    if config.log_file is not None:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
