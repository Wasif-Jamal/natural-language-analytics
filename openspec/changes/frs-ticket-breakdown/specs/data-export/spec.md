## ADDED Requirements

### Requirement: CSV export of query results
The UI SHALL provide a `st.download_button` in the results table area that downloads all returned rows as a CSV file. The CSV SHALL include column headers as the first row. No temporary files SHALL be written to disk — the CSV bytes SHALL be generated in-memory using `pandas.DataFrame.to_csv()`. The button SHALL only appear when a non-empty result set is present.

**FRS reference:** FR-13, FRS §8 (Reporting Requirements)  
**Module:** `app.py`

#### Scenario: Download button produces a valid CSV
- **WHEN** a query returns `columns=["region", "revenue"]` and `rows=[("North", 500), ("South", 300)]`
- **THEN** clicking the download button produces a CSV file with header row `region,revenue` and two data rows

#### Scenario: CSV includes column headers
- **WHEN** the CSV is generated
- **THEN** the first row of the file matches the `columns` list from the query result

#### Scenario: Download button is absent when result is empty
- **WHEN** `EmptyResultError` was raised and no rows are available
- **THEN** no CSV download button is rendered

#### Scenario: No temporary files are written to disk
- **WHEN** the CSV download button is rendered
- **THEN** no file is created in the filesystem (CSV bytes are passed directly to `st.download_button`)

---

### Requirement: PNG export of rendered chart
The UI SHALL provide a `st.download_button` in the visualization area that downloads the rendered Matplotlib figure as a PNG image. The PNG bytes SHALL be generated in-memory using `figure.savefig(buf, format="png")`. The button SHALL only appear when `ChartResult["type"] == "figure"`.

**FRS reference:** FR-14, FRS §8 (Reporting Requirements)  
**Module:** `app.py`

#### Scenario: PNG download button appears for figure results
- **WHEN** `ChartResult["type"] == "figure"`
- **THEN** a "Download PNG" `st.download_button` is rendered below the chart

#### Scenario: PNG download button is absent for text results
- **WHEN** `ChartResult["type"] == "text"`
- **THEN** no PNG download button is rendered

#### Scenario: PNG download button is absent for table results
- **WHEN** `ChartResult["type"] == "table"`
- **THEN** no PNG download button is rendered

#### Scenario: PNG bytes are generated in-memory
- **WHEN** the PNG export is triggered
- **THEN** `figure.savefig` writes to a `BytesIO` buffer; no file is created on disk

---

### Requirement: Out of Scope for data-export
The export functionality SHALL NOT apply additional data transformations, filtering, or aggregation to the exported data. The exported CSV SHALL reflect the raw query result rows as returned by `sql_executor.run`. The exported PNG SHALL be the exact chart rendered by `chart_engine.render` — no re-rendering.

#### Scenario: CSV exports all returned rows without modification
- **WHEN** the query returns 500 rows
- **THEN** the CSV file contains all 500 rows (subject to `MAX_RESULT_ROWS` cap applied by `sql_executor.run`)

#### Scenario: No server-side file storage
- **WHEN** both export buttons are used
- **THEN** no files are stored on the server; all data is streamed directly to the browser via Streamlit's download mechanism
