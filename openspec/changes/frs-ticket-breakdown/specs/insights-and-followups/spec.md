## ADDED Requirements

### Requirement: LLM-generated actionable insights
`insight_engine.generate(question: str, columns: list[str], rows: list[tuple], llm_client: LLMClient) -> dict` SHALL call `LLMClient.complete` with a result summary containing the top 10 rows and basic aggregates (min, max, sum, mean for numeric columns). It SHALL NOT pass the full result set to the LLM. The system prompt SHALL instruct the LLM to return valid JSON only, in the form `{"insights": [...], "suggested_questions": [...]}`. The function SHALL return this parsed dict.

**FRS reference:** FR-9, FR-10, FR-11 (FRS §6.4, §6.5)  
**Module:** `services/insight_engine.py`

#### Scenario: Successful call returns insights and suggested_questions
- **WHEN** `generate("Top products by revenue", ["product", "revenue"], rows, llm_client)` is called and the LLM returns valid JSON
- **THEN** the function returns a dict with keys `"insights"` (list of strings) and `"suggested_questions"` (list of strings)

#### Scenario: Insights list contains 2–4 entries
- **WHEN** the LLM returns valid JSON with `"insights"`
- **THEN** the returned insights list contains between 2 and 4 items (as instructed in the prompt)

#### Scenario: Suggested questions list contains exactly 3 entries
- **WHEN** the LLM returns valid JSON with `"suggested_questions"`
- **THEN** the returned list contains exactly 3 items

#### Scenario: Only top 10 rows are passed to LLM
- **WHEN** `rows` contains 500 items
- **THEN** the user message passed to `llm_client.complete` contains at most 10 rows of data

#### Scenario: Aggregates are included in the LLM prompt
- **WHEN** `columns` includes a numeric column `"revenue"`
- **THEN** the user message includes computed min, max, sum, and mean for that column

#### Scenario: Unparseable JSON from LLM raises InsightError
- **WHEN** the LLM returns a non-JSON response (e.g. plain text)
- **THEN** `generate` raises `InsightError`

#### Scenario: LLM API failure raises InsightError
- **WHEN** `llm_client.complete` raises an exception
- **THEN** `generate` wraps and re-raises it as `InsightError`

#### Scenario: InsightError is non-fatal — insights panel is skipped
- **WHEN** `app.py` catches `InsightError`
- **THEN** the insights panel is silently hidden; no error message is shown to the user; the rest of the result (chart, table, history) is still rendered

---

### Requirement: Suggested follow-up questions as clickable buttons
The UI SHALL render each suggested follow-up question as a `st.button`. Clicking one SHALL re-submit that question string as a new query, replacing the current result. The buttons SHALL appear after the chart/answer panel and before the results table.

**FRS reference:** FR-11, FRS §4 (Suggested Questions)  
**Module:** `app.py`

#### Scenario: Three follow-up buttons are rendered after successful insight generation
- **WHEN** `insight_engine.generate` returns 3 suggested questions
- **THEN** `app.py` renders exactly 3 `st.button` elements for those questions

#### Scenario: Clicking a follow-up button re-runs the pipeline
- **WHEN** the user clicks a suggested question button
- **THEN** the pipeline is triggered with that question as the new input

#### Scenario: Follow-up buttons do not appear when InsightError is raised
- **WHEN** `InsightError` is raised
- **THEN** no follow-up question buttons are rendered

---

### Requirement: Out of Scope for insights-and-followups
`insight_engine.py` SHALL NOT execute SQL, access the database, or import SQLAlchemy. Insights SHALL be derived strictly from the data returned by the query — the engine MUST NOT invent figures, trends, or claims not present in the provided rows and aggregates.

#### Scenario: No database access in insight_engine.py
- **WHEN** `services/insight_engine.py` is inspected for imports
- **THEN** no import of `sqlalchemy` is present

#### Scenario: No provider SDK import in insight_engine.py
- **WHEN** `services/insight_engine.py` is inspected for imports
- **THEN** no import of `anthropic`, `openai`, `google.genai`, or direct HTTP client for Ollama is present
