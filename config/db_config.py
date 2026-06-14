from __future__ import annotations

from sqlalchemy import create_engine as _sa_create_engine
from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.env_config import AppConfig

MAX_RESULT_ROWS: int = 10_000


def get_engine(config: AppConfig) -> Engine:
    global MAX_RESULT_ROWS
    MAX_RESULT_ROWS = config.max_result_rows
    engine = _sa_create_engine(config.database_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine
