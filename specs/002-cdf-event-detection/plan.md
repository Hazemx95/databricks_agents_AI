# Implementation Plan: CDF Event Detection (Phase 002)

**Branch**: `002-cdf-event-detection` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-cdf-event-detection/spec.md`

## Summary

Consume the Delta Change Data Feed of `databricks_arrow_cata.bronz.sales_info`, detect changes to the watched column `sls_price`, shape each detected change into a structured event matching the existing `databricks_arrow_cata.monitoring.change_events` schema, and persist events via an idempotent `MERGE` so re-runs add zero duplicates. Delivery is three artifacts plus tests:

1. `src/cdf_agent_monitoring/event_builder.py` — pure-Python (no Spark) helpers: `calculate_change_percent`, `build_business_key`, `build_json_from_columns`.
2. `tests/test_event_builder.py` — unit tests for the helpers, runnable locally without Databricks.
3. `notebooks/02_run_cdf_detection.py` — serverless notebook: validate CDF → read `table_changes()` → filter pre/post images → pair by `sls_ord_num` + `_commit_version` → detect `sls_price` change → build event rows → `MERGE` into `change_events` → display every stage → print SUCCESS or a clear no-new-events message.

This phase **detects and persists events only**. No CDF enablement, no source mutation, no severity classification, no alerts, no notification logs, no Genie/LLM.

## Technical Context

**Language/Version**: Python 3.12 (Databricks notebook source + pure-Python helper module) + Spark SQL (Delta Lake `table_changes()` + `MERGE`).

**Primary Dependencies**: Databricks serverless Spark runtime; Delta Lake CDF; project `src/cdf_agent_monitoring/config.py` for shared constants. The `event_builder` module has **zero third-party dependencies** (standard library only — `json`) and **no Spark dependency**, so it is unit-testable on a laptop. No LangChain/OpenAI/RAG/Genie.

**Storage**: Reads the CDF of `databricks_arrow_cata.bronz.sales_info` (read-only — never the table data itself mutated). Writes (insert-only via `MERGE`) to `databricks_arrow_cata.monitoring.change_events` (existing 13-column Delta table). No schema changes.

**Testing**: `pytest` for the pure-Python helpers (local, no Databricks). Notebook self-validates against the live workspace (FR-018) and prints a PASS/no-events status; `quickstart.md` documents the runnable end-to-end scenario.

**Target Platform**: Databricks Free Edition, serverless compute only.

**Project Type**: Databricks data-engineering project — notebooks in `notebooks/`, shared package in `src/cdf_agent_monitoring/`, unit tests in `tests/`, SQL in `sql/`.

**Performance Goals**: Not performance-sensitive. CDF window over a small bronze table; single MERGE. Completes in seconds-to-minutes on serverless.

**Constraints**: Serverless only; no classic clusters; no hardcoded secrets; no external network calls. Idempotent persistence is mandatory (constitution IV). `event_builder` must remain Spark-free.

**Scale/Scope**: One source table, one watched column (`sls_price`), one rule (`SALES_PRICE_CHANGE_001`). Three deliverable files + tests; optional README touch-up.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Free Edition / Serverless Constraints | PASS | All Spark work runs serverless; helpers are stdlib-only. No secrets, no external calls. |
| II. Delta CDF Events | PASS | This phase is the canonical implementation of CDF→structured-event. Every required event field (`business_key`, `watched_column`, `old_value`, `new_value`, `change_percent`, `commit_version`, `commit_timestamp`) is produced. Raw CDF rows are not streamed downstream — only structured events are persisted. |
| III. Rule-Based Agent (No LLM) | PASS (N/A) | No severity/decision logic in this phase (correctly deferred to Phase 003). No LLM. |
| IV. Data Safety & Idempotency | PASS | `MERGE` keyed on (`rule_id`, business key, `watched_column`, `commit_version`) with insert-only `WHEN NOT MATCHED`. Re-run inserts zero rows (SC-004). Source table never modified. |
| V. Audit & Observability | PASS | Events land in `change_events` with full provenance (`commit_version`, `commit_timestamp`, `created_at`, `event_id`). Notebook displays every stage and prints an unambiguous status. (`agent_run_log` write remains deferred to the agent-workflow phases, consistent with Phase 001.) |

**Gate result**: PASS. No violations; Complexity Tracking not required.

**Post-design re-check**: PASS — design artifacts add no new dependencies, no new tables, and no external calls; idempotency and the Spark-free helper boundary are preserved.

## Project Structure

### Documentation (this feature)

```text
specs/002-cdf-event-detection/
├── plan.md              # This file
├── spec.md              # Feature specification (present)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── event_builder.md       # Contract for the pure-Python helpers
│   └── notebook-contract.md   # Behavioral contract for the detection notebook
└── checklists/
    └── requirements.md  # From /speckit-specify
```

### Source Code (repository root)

```text
src/cdf_agent_monitoring/
├── config.py            # REUSE: SOURCE_TABLE, EVENTS_TABLE, RULE_ID, BUSINESS_KEY_COLUMNS,
│                        #        CONTEXT_COLUMNS, WATCHED_COLUMN (already present)
└── event_builder.py     # IMPLEMENT: calculate_change_percent, build_business_key,
                         #            build_json_from_columns (Spark-free, stdlib only)

tests/
└── test_event_builder.py  # IMPLEMENT: unit tests for the three helpers

notebooks/
└── 02_run_cdf_detection.py  # IMPLEMENT: full validate→read→pair→detect→build→merge→display flow

README.md                  # OPTIONAL: add a Phase 002 run note if needed
```

**Structure Decision**: Follow the established convention exactly (Phase 000/001). Constants live in `config.py` and are imported by both the helper module and the notebook (notebook adds `src/` to `sys.path`, mirroring `notebooks/01_enable_cdf_and_validate.py`). The detection logic that needs Spark stays in the notebook; the pure value/JSON logic lives in `event_builder.py` so it is unit-testable without a cluster. The notebook reuses the `[RUN]`/`[OK]`, `run_sql`, and `display(...)` patterns already in notebook 01.

## Key Design Decisions (see research.md for full rationale)

- **Event-row schema is fixed by the existing table.** The user-supplied field list (`business_key`, `change_type`, `event_status`, `source_table_full_name`) includes names that are **not** columns of `change_events`. Per FR-010 (match schema exactly) and the out-of-scope rule (no schema changes), the notebook builds an internal working DataFrame that may carry helper columns (`business_key` string, `change_type`) for the MERGE join, but the **persisted columns are exactly the 13 schema columns**. `source_table` holds the fully-qualified name; `event_status` is dropped (no such column).
- **Deduplication.** The constitutional key is (`rule_id`, business key, `watched_column`, `commit_version`). Since `change_events` stores the key as `business_key_json`, the MERGE `ON` condition matches on `rule_id`, `business_key_json`, `watched_column`, `commit_version`, which is equivalent to matching on `sls_ord_num` (the business key is a deterministic JSON of `sls_ord_num`).
- **`change_percent` semantics.** Signed `((new-old)/old)*100`. Helper returns `None` when old/new is null, non-numeric, or old is zero (avoids divide-by-zero, FR-007). `None` maps to SQL `NULL` in the DOUBLE column.
- **CDF version inputs.** Notebook widgets `start_version` / `end_version`. If `end_version` is blank, read from `start_version` to the latest available version.
