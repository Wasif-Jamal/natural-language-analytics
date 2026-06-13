## ADDED Requirements

### Requirement: Result shape detection
`chart_engine.render(columns: list[str], rows: list[tuple], question: str) -> ChartResult` SHALL detect the shape of the result set and select the appropriate presentation. Detection logic (evaluated in order):

1. `1 row × 1 column` → plain-language sentence
2. One column has a date/time type → line chart
3. Exactly two numeric columns → scatter plot
4. One categorical + one measure, values sum ≈ 100% (within ±5%) → pie chart
5. One categorical + one measure (general) → bar chart
6. All other shapes → table only

**FRS reference:** FR-6, FRS §5 (Result Presentation Rules)  
**Module:** `services/chart_engine.py`

#### Scenario: 1×1 result triggers text presentation
- **WHEN** `columns=["total_revenue"]` and `rows=[(1500000,)]`
- **THEN** `render` returns `{"type": "text", "text": <sentence containing the value>}`

#### Scenario: Time column + measure triggers line chart
- **WHEN** `columns=["month", "revenue"]` and `rows` contain date strings and floats
- **THEN** `render` returns `{"type": "figure", "figure": <matplotlib.Figure>}` rendered as a line chart

#### Scenario: Two numeric columns trigger scatter plot
- **WHEN** `columns=["revenue", "profit"]` and all row values are numeric
- **THEN** `render` returns `{"type": "figure", "figure": <matplotlib.Figure>}` rendered as a scatter plot

#### Scenario: Categorical + measure summing to ~100% triggers pie chart
- **WHEN** `columns=["region", "share"]` and measure values sum to approximately 100%
- **THEN** `render` returns `{"type": "figure", "figure": <matplotlib.Figure>}` rendered as a pie chart

#### Scenario: Categorical + measure (general) triggers bar chart
- **WHEN** `columns=["product", "revenue"]` and measure values do NOT sum to ~100%
- **THEN** `render` returns `{"type": "figure", "figure": <matplotlib.Figure>}` rendered as a bar chart

#### Scenario: Ambiguous shape falls back to table
- **WHEN** `columns=["id", "name", "city", "status"]` (multiple string columns, no clear measure)
- **THEN** `render` returns `{"type": "table"}`

---

### Requirement: ChartResult type contract
`chart_engine.render` SHALL return a typed `ChartResult` dict. The `type` field SHALL be one of `"figure"`, `"text"`, or `"table"`. `app.py` SHALL switch on `ChartResult["type"]` to render — no `isinstance` checks on raw data. All six shape branches MUST be tested.

**FRS reference:** FR-7, FR-8  
**Module:** `services/chart_engine.py`, `app.py`

#### Scenario: Figure result rendered with st.pyplot
- **WHEN** `ChartResult["type"] == "figure"`
- **THEN** `app.py` calls `st.pyplot(result["figure"])` and offers a PNG download button

#### Scenario: Text result rendered with st.metric or st.write
- **WHEN** `ChartResult["type"] == "text"`
- **THEN** `app.py` renders `result["text"]` as a plain-language answer panel

#### Scenario: Table result renders data table only (no chart)
- **WHEN** `ChartResult["type"] == "table"`
- **THEN** `app.py` renders only the results table with no visualization panel

#### Scenario: All six shape branches are covered by tests
- **WHEN** the pytest suite runs
- **THEN** all six shape-detection paths in `chart_engine.py` have at least one passing test case

---

### Requirement: Out of Scope for result-presentation
`chart_engine.py` SHALL NOT call any LLM, access the database, or write files to disk. It SHALL NOT access `st.session_state`. PNG export is handled in `app.py` via `st.download_button`, not inside `chart_engine`.

#### Scenario: No database or LLM access in chart_engine.py
- **WHEN** `services/chart_engine.py` is inspected for imports
- **THEN** no import of `sqlalchemy`, `LLMClient`, or any provider SDK is present

#### Scenario: No file I/O in chart_engine.py
- **WHEN** `chart_engine.render` is called
- **THEN** no files are written to disk (figure is returned in-memory as a `matplotlib.Figure` object)
