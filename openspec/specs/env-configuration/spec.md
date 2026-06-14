# Spec: env-configuration

## Purpose

Defines the structure, content, and constraints of `.env.example` — the repository's canonical template for environment variable configuration. Covers required variables, optional variables, provider-specific exceptions, file structure, and what must not appear in the file.

---

## Requirements

### Requirement: .env.example documents all required environment variables

`.env.example` SHALL exist at the repository root and SHALL declare all required environment variables with documented placeholder values. Required vars are those whose absence causes a fatal startup error in `env_config.py`.

Required vars: `DATABASE_URL`, `LLM_PROVIDER`, `LLM_API_KEY`.

**FRS reference:** SDS §4.1, §4.2, §4.3  
**File:** `.env.example`

#### Scenario: DATABASE_URL is present with a documented example

- **WHEN** `.env.example` is inspected
- **THEN** `DATABASE_URL` is present and set to a valid SQLite example value (e.g. `sqlite:///data/sales.db`)

#### Scenario: LLM_PROVIDER is present with valid options documented

- **WHEN** `.env.example` is inspected
- **THEN** `LLM_PROVIDER` is present and an inline comment lists all valid values: `anthropic`, `openai`, `gemini`, `ollama`

#### Scenario: LLM_API_KEY is present with a placeholder and Ollama exception noted

- **WHEN** `.env.example` is inspected
- **THEN** `LLM_API_KEY` is present with a placeholder value and an inline comment states it is not required when `LLM_PROVIDER=ollama`

---

### Requirement: .env.example documents all optional environment variables

`.env.example` SHALL declare all optional environment variables with their default values shown. Optional vars are those with a fallback if absent.

Optional vars: `LLM_MODEL`, `MAX_RESULT_ROWS` (default `10000`), `LOG_LEVEL` (default `INFO`), `LOG_FILE` (default none).

**FRS reference:** SDS §4.2, §4.3, §4.4  
**File:** `.env.example`

#### Scenario: LLM_MODEL is present as an empty optional override

- **WHEN** `.env.example` is inspected
- **THEN** `LLM_MODEL` is present with an empty value and an inline comment lists the default model per provider (anthropic → `claude-sonnet-4-6`, openai → `gpt-4o`, gemini → `gemini-2.0-flash`)

#### Scenario: MAX_RESULT_ROWS shows its default

- **WHEN** `.env.example` is inspected
- **THEN** `MAX_RESULT_ROWS` is present and set to `10000`

#### Scenario: LOG_LEVEL shows its default

- **WHEN** `.env.example` is inspected
- **THEN** `LOG_LEVEL` is present and set to `INFO`; an inline comment lists valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`

#### Scenario: LOG_FILE is present as empty optional

- **WHEN** `.env.example` is inspected
- **THEN** `LOG_FILE` is present with an empty value and an inline comment states it defaults to stdout when blank

---

### Requirement: .env.example documents the GEMINI_API_KEY provider exception

`.env.example` SHALL document `GEMINI_API_KEY` as a commented-out line alongside `LLM_API_KEY`. Per SDS §5.6, the Google Gemini SDK expects `GEMINI_API_KEY` by name rather than `LLM_API_KEY`.

**FRS reference:** SDS §5.6 (LLMClient — Gemini provider)  
**File:** `.env.example`

#### Scenario: GEMINI_API_KEY appears as a commented-out line

- **WHEN** `.env.example` is inspected
- **THEN** a commented-out `GEMINI_API_KEY` line is present in the LLM section with a note that it is required when `LLM_PROVIDER=gemini`

---

### Requirement: .env.example is structured in grouped sections

`.env.example` SHALL organise variables into three clearly labelled sections matching SDS §4 subsections: Database, LLM, and Logging. A header comment SHALL explain how to use the file.

**FRS reference:** SDS §4.1–4.4  
**File:** `.env.example`

#### Scenario: File contains three section headers

- **WHEN** `.env.example` is inspected
- **THEN** three section comment headers are present: one for database config, one for LLM config, one for logging config

#### Scenario: File contains a usage header comment

- **WHEN** `.env.example` is inspected
- **THEN** the first lines include a comment explaining that the file should be copied to `.env` and that `.env` must not be committed

---

### Requirement: Out of Scope for env-configuration

`.env.example` SHALL NOT contain actual credentials, real API keys, or database passwords. Runtime validation logic SHALL NOT be placed in `.env.example`. The Ollama base URL SHALL NOT appear — no env var for it is defined in the SDS.

#### Scenario: No real credentials present

- **WHEN** `.env.example` is inspected
- **THEN** all credential fields contain placeholder strings (e.g. `your-api-key-here`) or are blank — no real API keys, tokens, or passwords are present
