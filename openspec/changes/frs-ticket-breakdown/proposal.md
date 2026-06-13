## Why

The FRS for the Natural Language Analytics Dashboard is fully approved, but no implementation tickets exist yet. Developers cannot begin work without clear, atomic tickets that specify requirements, acceptance criteria, error scenarios, and scope boundaries for each functional area.

## What Changes

- Break FRS §3 (Functional Requirements) into individual implementation tickets, one per logical unit of work
- Each ticket links explicitly to its FRS requirement ID(s)
- Each ticket defines numbered acceptance criteria, error scenarios with expected outcomes, and an out-of-scope section
- No new functional requirements are introduced — this is a planning artifact only

## Capabilities

### New Capabilities

- `nl-query-input`: User submits natural-language questions via a text input field (FR-1)
- `nl-to-sql`: LLM-based translation of a natural-language question into a validated SQL SELECT statement (FR-2, FR-3, FR-4)
- `sql-execution`: Validated SQL execution against the configured database with result retrieval (FR-5)
- `result-presentation`: Shape detection and appropriate rendering — chart, plain-language sentence, or table (FR-6, FR-7, FR-8)
- `insights-and-followups`: LLM-generated actionable insights and suggested follow-up questions from result data (FR-9, FR-10, FR-11 / FRS §3 FR-10, FR-11)
- `query-history`: Session-level history of executed questions with re-run support (FR-12)
- `data-export`: CSV export of query results and PNG export of rendered charts (FR-13, FR-14)
- `config-bootstrap`: Project bootstrap — env var loading, DB engine creation, LLM client initialisation, schema introspection (SDS §3–4)
- `error-handling`: Typed exception hierarchy and exact user-facing error messages for all five failure scenarios (FRS §7)

### Modified Capabilities

_(none — greenfield project, no existing specs)_

## Impact

- Creates `openspec/changes/frs-ticket-breakdown/specs/<capability>/spec.md` for each capability above
- No code changes in this change — planning artifacts only
- Unblocks all implementation branches once tasks.md is approved
