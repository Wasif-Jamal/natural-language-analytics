## ADDED Requirements

### Requirement: Session-level query history storage
`history.append(question: str, sql: str)` SHALL add an entry `{"question": str, "sql": str, "timestamp": str}` to `st.session_state["query_history"]`. `history.get_all()` SHALL return the list in reverse-chronological order (most recent first). `history.clear()` SHALL reset the list to `[]`. History is in-memory only and does NOT persist across Streamlit page refreshes or server restarts.

**FRS reference:** FR-12, FRS §4 (Query History Panel), SDS §5.5  
**Module:** `services/history.py`

#### Scenario: append adds an entry to session state
- **WHEN** `history.append("Show revenue by region", "SELECT region, SUM(revenue) FROM orders GROUP BY region")` is called
- **THEN** `st.session_state["query_history"]` contains one entry with `question`, `sql`, and `timestamp` keys

#### Scenario: get_all returns most recent entry first
- **WHEN** three questions have been appended in order: A, B, C
- **THEN** `history.get_all()` returns `[C, B, A]`

#### Scenario: clear resets the list
- **WHEN** `history.clear()` is called after two entries have been appended
- **THEN** `history.get_all()` returns `[]`

#### Scenario: History is empty on first bootstrap
- **WHEN** `starter.py` runs and `query_history` is initialised
- **THEN** `history.get_all()` returns `[]`

---

### Requirement: Query history UI with re-run
The UI SHALL display previously executed questions in an expandable history panel. Each history entry SHALL show the question text and its timestamp. Each entry SHALL have a "Re-run" button that re-submits the question as a new query.

**FRS reference:** FR-12, FRS §4 (Query History Panel)  
**Module:** `app.py`

#### Scenario: History panel shows all previous questions
- **WHEN** three queries have been executed in the session
- **THEN** the history expander lists all three, most recent first

#### Scenario: Re-run button re-submits the question
- **WHEN** the user clicks "Re-run" for a history entry
- **THEN** the pipeline is triggered with that entry's `question` string

#### Scenario: History panel is hidden when history is empty
- **WHEN** no queries have been executed
- **THEN** the history panel is not rendered (or renders as empty with an appropriate message)

---

### Requirement: Out of Scope for query-history
`history.py` SHALL NOT persist data to disk, a database, or any external system. It SHALL NOT call the LLM or execute SQL. History is session-scoped only.

#### Scenario: No file or database writes in history.py
- **WHEN** `services/history.py` is inspected for I/O operations
- **THEN** no file open, SQLAlchemy write, or external API call is present

#### Scenario: History does not persist across page refresh
- **WHEN** the Streamlit app page is refreshed (triggering a full rerender)
- **THEN** `query_history` is re-initialised to `[]` by `starter.py` (session state does not survive hard refresh)
