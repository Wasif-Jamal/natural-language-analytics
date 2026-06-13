## Context

The Natural Language Analytics Dashboard FRS is fully approved (v1.0, 2026-06-12). The project is greenfield — no Python implementation exists. This design document covers the planning approach for decomposing the FRS into implementable tickets, not the system architecture itself (that is covered in SDS.md).

The repo has: `docs/FRS.md`, `docs/SDS.md`, `docs/nl-analytics-dashboard-spec.md`, `AGENTS.md`, `CLAUDE.md`. No `pyproject.toml`, no source files yet.

## Goals / Non-Goals

**Goals:**
- Produce one spec file per logical capability, covering requirements, acceptance criteria, error scenarios, and out-of-scope
- Map every FRS requirement ID to at least one spec scenario
- Produce a tasks.md that gives developers atomic, unambiguous implementation units
- Ensure the config/bootstrap layer is treated as its own capability (it has no FRS ID but is a prerequisite for everything)

**Non-Goals:**
- Changing any FRS requirements
- Deciding implementation order (that is a sprint-planning concern)
- Specifying database migrations (no existing DB to migrate)
- Covering auth, forecasting, or RBAC (explicitly out of FRS §11)

## Decisions

**Decision 1: 9 capabilities, one spec file each**

The FRS has 14 requirement IDs (FR-1 to FR-14) that cluster naturally into 9 logical groups. Splitting finer (e.g. one file per FR-ID) would create 14 thin files with heavy cross-referencing. Combining into capabilities keeps each spec self-contained and maps directly to a service module or config concern.

| Capability | FRS IDs | Module |
|---|---|---|
| `config-bootstrap` | — (SDS §3–4) | `starter.py`, `config/` |
| `nl-query-input` | FR-1 | `app.py` (input component) |
| `nl-to-sql` | FR-2, FR-3, FR-4 | `services/nl_to_sql.py` |
| `sql-execution` | FR-5 | `services/sql_executor.py` |
| `result-presentation` | FR-6, FR-7, FR-8 | `services/chart_engine.py` |
| `insights-and-followups` | FR-9, FR-10, FR-11 | `services/insight_engine.py` |
| `query-history` | FR-12 | `services/history.py` |
| `data-export` | FR-13, FR-14 | `app.py` (download buttons) |
| `error-handling` | FRS §7 | `app.py` (exception catch) |

**Decision 2: Each spec uses ADDED Requirements only**

All capabilities are new (greenfield). No `openspec/specs/` directory exists. Every spec uses `## ADDED Requirements` exclusively.

**Decision 3: Error scenarios are first-class scenarios**

Per user requirement ("Error scenarios: what should fail + expected result"), every spec includes at least one `#### Scenario:` that tests a failure path. These map directly to pytest test cases.

**Decision 4: Out-of-scope is embedded in each spec as a Requirement**

Rather than a free-text section, out-of-scope constraints are written as explicit `### Requirement: Out of Scope` blocks with `#### Scenario:` entries that assert the system does NOT do something. This makes them testable and prevents scope creep.

## Risks / Trade-offs

[Risk: `config-bootstrap` has no FRS ID] → Mitigation: Referenced to SDS §3–4 explicitly. Without this capability spec, the other eight are unimplementable. It is the critical path.

[Risk: `result-presentation` has 6 shape-detection branches] → Mitigation: Each branch gets its own `#### Scenario:`. AGENTS.md already mandates coverage of all six — the spec makes this contract explicit.

[Risk: `insights-and-followups` is LLM-non-deterministic] → Mitigation: Scenarios specify structural requirements (count, JSON shape, grounding rules) not content. Tests mock `LLMClient.complete`.

[Risk: `error-handling` error strings must match exactly] → Mitigation: Error strings are embedded verbatim in scenarios. Any deviation is a test failure.

## Migration Plan

No deployment steps — this is a planning-only change. Implementation begins when tasks.md is approved and a developer runs `/opsx:apply`.

## Open Questions

_(none — all FRS sections are fully specified)_
