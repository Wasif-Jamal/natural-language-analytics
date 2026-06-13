## ADDED Requirements

### Requirement: Natural-language question input field
The system SHALL render a text input field in the Streamlit UI that accepts a natural-language question from the user. The field SHALL support multi-line input. An "Execute" button SHALL trigger the full query pipeline. Submitting an empty question SHALL display an inline warning and NOT trigger the pipeline.

**FRS reference:** FR-1, FRS §4 (Question Input, Execute Button)  
**Module:** `app.py`

#### Scenario: Non-empty question triggers pipeline
- **WHEN** the user enters a non-empty question and clicks Execute
- **THEN** the query pipeline is invoked with that question string

#### Scenario: Empty question does not trigger pipeline
- **WHEN** the user clicks Execute with an empty input field
- **THEN** an inline warning is displayed and `nl_to_sql.generate` is NOT called

#### Scenario: Suggested follow-up question re-submits as new query
- **WHEN** the user clicks a suggested follow-up question button
- **THEN** that question string is submitted to the pipeline as a new query (not appended to the input field; the current result is replaced)

#### Scenario: Question input field is visible on page load
- **WHEN** the Streamlit app loads for the first time
- **THEN** the question input field and Execute button are rendered without errors

---

### Requirement: Out of Scope for nl-query-input
The question input component SHALL NOT perform SQL generation, validation, or execution. It SHALL NOT access `db_engine`, `llm_client`, or `db_schema` directly.

#### Scenario: No direct SDK calls from app.py input handler
- **WHEN** the Execute button handler runs
- **THEN** it delegates to `nl_to_sql.generate` — it does not import or call any LLM provider SDK directly
