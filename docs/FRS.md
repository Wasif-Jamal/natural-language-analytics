# Functional Requirements Specification
# Natural Language Analytics Dashboard

| Field | Value |
|---|---|
| **Project** | Natural Language Analytics Dashboard |
| **Version** | 1.0 |
| **Date** | 2026-06-12 |
| **Status** | Approved |
| **Source of Truth** | docs/nl-analytics-dashboard-spec.md |

---

## 1. Purpose

This document specifies the functional requirements for the Natural Language Analytics Dashboard — a Streamlit application that allows business users to query structured SQL data using plain English and receive results as charts, written answers, actionable insights, and suggested follow-up questions.

---

## 2. User Personas

| Persona | Primary Need | Representative Questions |
|---|---|---|
| **Business Analyst** | Quick metrics and trends without SQL knowledge | Monthly revenue this year; top products by revenue; revenue by region |
| **Operations Manager** | Operational visibility into orders, products, and regions | Orders by month; product performance by category; revenue distribution by region |
| **Product Manager** | Product-level reporting and category breakdowns | Top performing products; product revenue trends; category-wise sales breakdown |

---

## 3. Functional Requirements

| ID | Requirement | Notes |
|---|---|---|
| FR-1 | Users shall submit natural-language questions via a text input field | Plain English; no SQL knowledge required |
| FR-2 | The system shall generate a valid SQL SELECT query corresponding to the user's question | LLM-generated; schema context injected into prompt |
| FR-3 | The system shall display the generated SQL query to the user before execution | For transparency, debugging, and validation |
| FR-4 | The system shall validate the generated SQL and reject any non-read-only statements | See §6 for blocked operations |
| FR-5 | The system shall execute validated SQL queries against the configured database | Read-only; results returned as tabular data |
| FR-6 | The system shall detect the shape of the result set and select the appropriate presentation | See §5 for shape-to-presentation mapping |
| FR-7 | The system shall render a Matplotlib chart for multi-row results | Bar, line, pie, or scatter depending on result shape |
| FR-8 | The system shall present single-value results as a plain-language sentence | e.g. "Total revenue for this quarter is 200K USD" |
| FR-9 | The system shall display returned data in a paginated, sortable tabular format | Alongside the chart or written answer |
| FR-10 | The system shall generate actionable insights derived strictly from the returned data | No fabricated figures or unsupported claims |
| FR-11 | The system shall suggest relevant follow-up questions based on the current result | Presented as one-click prompts that re-run as new queries |
| FR-12 | The system shall maintain a session-level query history | Previously executed questions are viewable and re-runnable |
| FR-13 | Users shall be able to export query results as a CSV file | Via a download button in the results table |
| FR-14 | Users shall be able to export the rendered chart as a PNG file | Via a download button in the visualization area |

---

## 4. User Interface Requirements

| Component | Requirement |
|---|---|
| **Question Input** | Single-line or multi-line text field for natural-language questions |
| **Execute Button** | Triggers the full query pipeline |
| **SQL Display** | Expandable code block showing the generated SQL |
| **Visualization Area** | Displays a Matplotlib chart or a plain-language answer panel for single-value results |
| **Insights Panel** | Displays 2–4 plain-language insights derived from the returned data |
| **Suggested Questions** | Displays 3 clickable follow-up questions rendered as buttons; clicking re-runs as a new query |
| **Results Table** | Paginated, sortable table of raw query results with a CSV download button |
| **Query History Panel** | Expandable list of previously executed questions with re-run buttons |

---

## 5. Result Presentation Rules

The system selects the presentation format based on the shape of the returned dataset:

| Result Shape | Presentation |
|---|---|
| Single value (1 row × 1 column) | Plain-language sentence / metric card |
| Time column + measure | Line chart |
| Two numeric columns | Scatter plot |
| Categorical column + measure, values sum ≈ 100% | Pie chart |
| Categorical column + measure (general) | Bar chart |
| All other shapes | Table only |

---

## 6. Validation Requirements

Only read-only SQL operations are permitted. The system must reject any query containing the following statements:

`INSERT` · `UPDATE` · `DELETE` · `DROP` · `ALTER` · `TRUNCATE`

Validation is applied in two layers:
1. Keyword block list (case-insensitive, whole-word match)
2. SQL AST parse check asserting the root node is a SELECT statement

---

## 7. Error Handling Requirements

| Scenario | User-Facing Message |
|---|---|
| Question references unknown entities | `Unable to identify requested entities.` |
| Generated SQL fails validation | `Generated query could not be validated.` |
| Query returns no rows | `No data found for the requested query.` |
| Database connection or execution error | `Unable to retrieve data at this time.` |
| LLM API unavailable | `Unable to process your question at this time. Please try again.` |

All errors are displayed inline in the Streamlit UI; no raw stack traces are shown to users.

---

## 8. Reporting Requirements

| Output | Format | Trigger |
|---|---|---|
| Query results | CSV | Download button in results table |
| Visualization | PNG | Download button in visualization area |

---

## 9. Non-Functional Requirements

| Attribute | Requirement |
|---|---|
| **Performance** | Typical end-to-end query response under 10 seconds; supports datasets up to 1 million records |
| **Reliability** | Application recovers gracefully from query failures without crashing or requiring restart |
| **Insight accuracy** | Insights and written answers must reflect the actual returned data; no fabricated figures or unsupported claims |
| **Usability** | No SQL knowledge required; all interactions available through the Streamlit UI |
| **Maintainability** | All major functionality documented before implementation; config separated from business logic |
| **Security** | Non-read-only SQL statements are blocked before execution; no credentials exposed in the UI |

---

## 10. Assumptions

- The database schema is known and available before implementation begins.
- Users have read-only access to the data; no writes are performed by the application.
- Data quality is outside the scope of this application.
- Authentication and authorization are outside scope; the application assumes a trusted user environment.

---

## 11. Out of Scope

| Item |
|---|
| Statistical forecasting and predictive modeling |
| ML-based recommendation engines |
| Autonomous actions or decisions on the user's behalf |
| Multi-database federation |
| User management and role-based access control |
| Dashboard sharing and collaboration features |

> Qualitative insights (§FR-10) and suggested follow-up questions (§FR-11) are in scope. What remains out of scope is *predictive* analytics and *automated action* — the system explains and recommends; it does not forecast or act.

---

## 12. Acceptance Criteria

The project is complete when all of the following are verified:

| Area | Criterion |
|---|---|
| **Querying** | Natural-language questions can be submitted; SQL is generated successfully; SQL executes successfully |
| **Visualization** | Bar, line, pie, and scatter charts render correctly from real data |
| **Results Presentation** | Single-value results display as plain-language sentences; multi-row results display as charts |
| **Insights** | Actionable insights are generated and grounded in the returned data; no invented figures |
| **Follow-up Questions** | Suggested questions are displayed and runnable with one click |
| **Results Table** | Data table displays correctly; CSV export produces a valid file |
| **Chart Export** | PNG export produces a valid image of the rendered chart |
| **Query History** | Session history is maintained; previously executed questions can be re-run |
| **Error Handling** | All error scenarios display the correct user-facing message; no raw errors shown |
| **Security** | Non-read-only SQL statements are blocked; write operations never reach the database |
| **Documentation** | FRS, SDS, and all referenced data contracts are complete before implementation begins |
