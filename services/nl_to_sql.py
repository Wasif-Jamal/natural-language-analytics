from __future__ import annotations

import re

import sqlglot

from config.llm_config import LLMClient
from services.exceptions import NLQueryError

_FENCE_RE = re.compile(r"```(?:sql)?\s*([\s\S]*?)```", re.IGNORECASE)

_SYSTEM_PROMPT_TEMPLATE = """\
You are a SQL expert. Generate a {dialect}-compatible SQL SELECT query \
for the schema below.

{schema_ddl}

Rules:
- Return a SELECT statement only.
- Do NOT use INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
- Return only the SQL — no explanation, no markdown fences, no comments."""


def _strip_fences(text: str) -> str:
    match = _FENCE_RE.search(text)
    return match.group(1).strip() if match else text.strip()


def _schema_to_ddl(schema: dict) -> str:
    lines = []
    for table, columns in schema.get("tables", {}).items():
        col_defs = ", ".join(f"{c['name']} {c['type']}" for c in columns)
        lines.append(f"CREATE TABLE {table} ({col_defs});")
    return "\n".join(lines)


def generate(question: str, schema: dict, llm_client: LLMClient) -> str:
    dialect = schema.get("dialect", "SQL")
    schema_ddl = _schema_to_ddl(schema)
    system = _SYSTEM_PROMPT_TEMPLATE.format(dialect=dialect, schema_ddl=schema_ddl)

    try:
        raw = llm_client.complete(system, question)
    except Exception as exc:
        raise NLQueryError(f"LLM API call failed: {exc}") from exc

    cleaned = _strip_fences(raw)

    if not cleaned.strip():
        raise NLQueryError("LLM returned an empty response")

    try:
        parsed = sqlglot.parse_one(cleaned)
    except sqlglot.errors.ParseError as exc:
        raise NLQueryError(f"LLM response is not valid SQL: {exc}") from exc

    if not isinstance(parsed, sqlglot.exp.Select):
        raise NLQueryError(
            f"LLM returned a non-SELECT statement: {type(parsed).__name__}"
        )

    return cleaned
