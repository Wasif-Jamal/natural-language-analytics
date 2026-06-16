from unittest.mock import MagicMock

import pytest

from config.llm_config import LLMClient
from services.exceptions import NLQueryError
from services.nl_to_sql import generate


def make_llm_client(return_value: str = "SELECT 1") -> LLMClient:
    mock = MagicMock(spec=LLMClient)
    mock.complete.return_value = return_value
    return mock


@pytest.fixture
def sample_schema():
    return {
        "dialect": "sqlite",
        "tables": {
            "orders": [
                {"name": "id", "type": "INTEGER"},
                {"name": "region", "type": "TEXT"},
            ]
        },
    }


def test_valid_question_returns_clean_sql(sample_schema):
    result = generate(
        "Show all order ids", sample_schema, make_llm_client("SELECT id FROM orders")
    )
    assert result == "SELECT id FROM orders"


def test_markdown_fences_stripped(sample_schema):
    result = generate(
        "Show all orders",
        sample_schema,
        make_llm_client("```sql\nSELECT * FROM orders\n```"),
    )
    assert result == "SELECT * FROM orders"


def test_schema_tables_in_system_prompt(sample_schema):
    client = make_llm_client("SELECT id FROM orders")
    generate("Show orders", sample_schema, client)
    system_arg = client.complete.call_args[0][0]
    assert "CREATE TABLE orders" in system_arg


def test_dialect_in_system_prompt(sample_schema):
    client = make_llm_client("SELECT id FROM orders")
    generate("Show orders", sample_schema, client)
    system_arg = client.complete.call_args[0][0]
    assert "sqlite" in system_arg.lower()


def test_empty_response_raises_nl_query_error(sample_schema):
    with pytest.raises(NLQueryError):
        generate("Show orders", sample_schema, make_llm_client(""))


def test_whitespace_response_raises_nl_query_error(sample_schema):
    with pytest.raises(NLQueryError):
        generate("Show orders", sample_schema, make_llm_client("   \n  "))


def test_unparseable_response_raises_nl_query_error(sample_schema):
    with pytest.raises(NLQueryError):
        generate("Show orders", sample_schema, make_llm_client("not SQL at all!!!"))


def test_non_select_raises_nl_query_error(sample_schema):
    with pytest.raises(NLQueryError):
        generate(
            "Show orders",
            sample_schema,
            make_llm_client("INSERT INTO orders VALUES (1, 'a')"),
        )


def test_llm_exception_raises_nl_query_error_with_cause(sample_schema):
    client = MagicMock(spec=LLMClient)
    client.complete.side_effect = RuntimeError("timeout")
    with pytest.raises(NLQueryError) as exc_info:
        generate("Show orders", sample_schema, client)
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_no_sqlalchemy_import():
    with open("services/nl_to_sql.py") as f:
        source = f.read()
    import_lines = "\n".join(
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    assert "sqlalchemy" not in import_lines


def test_no_provider_sdk_import():
    with open("services/nl_to_sql.py") as f:
        source = f.read()
    import_lines = "\n".join(
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    for forbidden in ("anthropic", "openai", "google.genai", "requests"):
        assert forbidden not in import_lines
