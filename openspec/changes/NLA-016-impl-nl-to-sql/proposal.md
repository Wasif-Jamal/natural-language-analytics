## Why

`nl_to_sql.py` is the entry point for every user query — it translates a plain-English question into the SQL string that drives the entire pipeline. Without it, `sql_executor.py` has nothing to validate or execute. The base spec in `frs-ticket-breakdown` defines the contract and scenarios, but four design decisions were deferred at planning time. This change resolves all four and provides the concrete implementation plan.

## What Changes

- Create `services/nl_to_sql.py` with `generate(question: str, schema: dict, llm_client: LLMClient) -> str`
- Serialize `schema["tables"]` to CREATE TABLE-style DDL strings for the system prompt
- Read `schema["dialect"]` (set by `starter.py`) to include a dialect-specific instruction in the system prompt
- Define a module-level `_SYSTEM_PROMPT_TEMPLATE` constant; build the final system string dynamically each call
- Strip markdown code fences (` ```sql … ``` ` and ` ``` … ``` `) from the LLM response before validation
- Raise `NLQueryError` immediately for empty/whitespace-only responses, before attempting sqlglot parsing
- Validate the cleaned SQL with `sqlglot.parse_one` and assert root node is `sqlglot.exp.Select`; raise `NLQueryError` on failure
- Wrap `llm_client.complete` exceptions with `raise NLQueryError(…) from e` to preserve original traceback in logs
- Create `tests/services/test_nl_to_sql.py` covering all spec scenarios with a mock `LLMClient`
- Add an import-guard test asserting no SQLAlchemy or provider SDK in the module

## Capabilities

### Modified Capabilities

- `nl-to-sql`: Resolves four deferred design decisions:
  1. Schema serialized as CREATE TABLE DDL (not JSON or ad-hoc text)
  2. DB dialect sourced from `schema["dialect"]` — no signature change, `starter.py` sets this key
  3. sqlglot validation asserts SELECT root node (defence-in-depth; `sql_executor` re-checks)
  4. Exception chaining (`raise NLQueryError(…) from e`) preserves original traceback for logging

## Impact

- Creates `services/nl_to_sql.py` and `tests/services/test_nl_to_sql.py`
- Requires `starter.py` (NLA-011) to set `schema["dialect"] = engine.dialect.name` when building `db_schema` — minor addition documented in the spec delta
- API contract `generate(question, schema, llm_client)` is unchanged from AGENTS.md
- Unblocks NLA-020 (`sql_executor.py`) — executor receives the SQL string returned by `generate`
- No changes to existing source files
