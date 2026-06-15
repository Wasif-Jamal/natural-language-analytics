class NLQueryError(Exception):
    """Raised by nl_to_sql when the LLM fails to produce valid SQL."""


class SQLValidationError(Exception):
    """Raised by sql_executor on blocked keyword or non-SELECT AST."""


class DBExecutionError(Exception):
    """Raised by sql_executor on database-level execution failure."""


class EmptyResultError(Exception):
    """Raised by sql_executor when the query returns zero rows."""


class InsightError(Exception):
    """Raised by insight_engine on unparseable LLM JSON or API error."""
