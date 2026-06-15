from __future__ import annotations

import logging

import streamlit as st
from sqlalchemy import inspect

from config.db_config import get_engine
from config.env_config import load_config
from config.llm_config import LLMClient
from config.log_config import setup_logging

logger = logging.getLogger(__name__)


def bootstrap() -> None:
    if "db_engine" in st.session_state:
        return

    config = load_config()
    setup_logging(config)

    logger.info("Bootstrapping application")

    engine = get_engine(config)
    llm_client = LLMClient(config)

    inspector = inspect(engine)
    db_schema: dict[str, list[dict]] = {}
    for table_name in inspector.get_table_names():
        db_schema[table_name] = [
            {"name": col["name"], "type": str(col["type"])}
            for col in inspector.get_columns(table_name)
        ]

    st.session_state["db_engine"] = engine
    st.session_state["llm_client"] = llm_client
    st.session_state["db_schema"] = db_schema
    st.session_state["query_history"] = []

    logger.info("Bootstrap complete — %d table(s) introspected", len(db_schema))
