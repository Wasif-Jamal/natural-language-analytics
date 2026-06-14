## Phase 1 — Foundation: Create .env.example

- [x] Create `.env.example` at repo root with a three-line usage header: project name, "copy to .env", "never commit .env"
- [x] Add `# --- Database ---` section with `DATABASE_URL=sqlite:///data/sales.db` and inline comment listing supported URL schemes (`sqlite:///`, `postgresql://`, `mysql+pymysql://`)
- [x] Add `# --- LLM ---` section with `LLM_PROVIDER=anthropic` and inline comment listing all valid values: `anthropic`, `openai`, `gemini`, `ollama`
- [x] Add `LLM_API_KEY=your-api-key-here` with inline comment noting it is not required when `LLM_PROVIDER=ollama`
- [x] Add commented-out `# GEMINI_API_KEY=your-gemini-api-key-here` with note that it is required when `LLM_PROVIDER=gemini` (SDS §5.6)
- [x] Add `LLM_MODEL=` (empty) with inline comment listing per-provider defaults: `anthropic → claude-sonnet-4-6`, `openai → gpt-4o`, `gemini → gemini-2.0-flash`
- [x] Add `MAX_RESULT_ROWS=10000` with inline comment stating it is optional with default `10000`
- [x] Add `# --- Logging ---` section with `LOG_LEVEL=INFO` and inline comment listing valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- [x] Add `LOG_FILE=` (empty) with inline comment stating it defaults to stdout when blank

**Phase 1 checkpoint:**
- [x] All 8 vars present: `DATABASE_URL`, `LLM_PROVIDER`, `LLM_API_KEY`, `GEMINI_API_KEY` (commented), `LLM_MODEL`, `MAX_RESULT_ROWS`, `LOG_LEVEL`, `LOG_FILE`
- [x] Three section headers present: `# --- Database ---`, `# --- LLM ---`, `# --- Logging ---`
- [x] No real credentials or API keys in the file — only placeholders or blank values

---

## Phase 2 — Quality Gates

```bash
uv run ruff format .     # no Python source changed; exits 0
uv run ruff check .      # exits 0, 0 errors
uv run pytest            # exits 5 (no tests collected — expected)
```

- [x] `uv run ruff format .` exits 0
- [x] `uv run ruff check .` exits 0 with 0 errors
- [x] `uv run pytest` exits 5

---

## Phase 3 — Scenario Verification (specs/env-configuration/spec.md)

One check per scenario declared in the spec delta:

- [x] **Scenario: DATABASE_URL present with example** — `DATABASE_URL=sqlite:///data/sales.db` present with supported-schemes comment
- [x] **Scenario: LLM_PROVIDER lists valid options** — `LLM_PROVIDER=anthropic` present; comment lists `anthropic`, `openai`, `gemini`, `ollama`
- [x] **Scenario: LLM_API_KEY notes Ollama exception** — `LLM_API_KEY` present with placeholder; comment states not required for `ollama`
- [x] **Scenario: LLM_MODEL shows per-provider defaults** — `LLM_MODEL=` present (empty); comment lists all three provider defaults
- [x] **Scenario: MAX_RESULT_ROWS shows default** — `MAX_RESULT_ROWS=10000` present
- [x] **Scenario: LOG_LEVEL shows default** — `LOG_LEVEL=INFO` present; comment lists all valid levels
- [x] **Scenario: LOG_FILE is empty optional** — `LOG_FILE=` present (empty); comment states stdout default
- [x] **Scenario: GEMINI_API_KEY as commented-out line** — `# GEMINI_API_KEY=` line present with `LLM_PROVIDER=gemini` note
- [x] **Scenario: Three section headers** — `# --- Database ---`, `# --- LLM ---`, `# --- Logging ---` all present
- [x] **Scenario: Usage header comment** — first lines include copy-to-.env and never-commit instructions
- [x] **Scenario: No real credentials** — grep confirms no real key patterns; all credential fields are placeholders or blank

**Phase 3 checkpoint:**
```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```
- [x] All three exit at expected codes (0, 0, 5)
