# Implementation Plan: Monitoring Rules Table (Phase 003)

**Branch**: `003-monitoring-rules` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-monitoring-rules/spec.md`

## Summary

Move the first monitoring rule from hardcoded constants into data. Phase 003 confirms `databricks_arrow_cata.monitoring.agent_rules` exists, upserts the single rule `SALES_PRICE_CHANGE_001` via an idempotent `MERGE` keyed on `rule_id`, validates the stored row against the expected source table and columns, displays the active rule, and prints an unambiguous `SUCCESS` / `FAILED` status. Delivery is three artifacts:

1. `sql/002_create_agent_rules.sql` — already present and correct; keep `CREATE TABLE IF NOT EXISTS` (safe to rerun). Append the canonical `MERGE` upsert as the reference SQL for the rule.
2. `notebooks/03_setup_monitoring_rules.py` — serverless notebook: header → title → constants → ensure table → `MERGE` upsert → display active rule → run validation checks → print `SUCCESS`/`FAILED`.
3. `src/cdf_agent_monitoring/config.py` — add the few rule constants not yet present (`RULE_NAME`, `EVENT_TYPE`, `CONDITION_TYPE`, `NOTIFICATION_TARGET_TYPE`, `NOTIFICATION_TARGET_VALUE`, and source-table parts) so the rule is defined once and reused.

This phase **stores and validates the rule only**. No CDF read, no source mutation, no event creation, no severity classification, no alerts, no notification-log rows, no Genie/LLM. Live-workspace grounding is already confirmed: the table exists with the expected 16 columns and currently holds **zero** rows, so the first run will insert exactly one.

## Technical Context

**Language/Version**: Python 3.12 (Databricks notebook source) + Spark SQL (Delta Lake `MERGE`). The rule constants live in a Spark-free `config.py` module.

**Primary Dependencies**: Databricks serverless Spark runtime; Delta Lake `MERGE INTO`; project `src/cdf_agent_monitoring/config.py` for shared constants. No third-party packages. No LangChain/OpenAI/RAG/Genie.

**Storage**: Writes (upsert via `MERGE`) to `databricks_arrow_cata.monitoring.agent_rules` (existing 16-column Delta table, PK `rule_id` NOT ENFORCED). No schema changes. Reads nothing from the source `bronz.sales_info` table (it is only *named* inside the rule's column values).

**Testing**: Validation is performed in-notebook against the live workspace (FR-013): assert exactly one active row for `SALES_PRICE_CHANGE_001` and assert each field equals its expected value, then print `SUCCESS`/`FAILED`. `quickstart.md` documents the runnable end-to-end scenario. No pure-Python helper module is required this phase (the logic is configuration + SQL), so no new `pytest` file is mandatory.

**Target Platform**: Databricks Free Edition, serverless compute only.

**Project Type**: Databricks data-engineering project — notebooks in `notebooks/`, shared package in `src/cdf_agent_monitoring/`, SQL in `sql/`.

**Performance Goals**: Not performance-sensitive. One-row `MERGE` and a handful of validation queries. Completes in seconds on serverless.

**Constraints**: Serverless only; no classic clusters; no hardcoded secrets; no external network calls. Idempotency is mandatory (constitution IV) — re-running must keep exactly one row. Thresholds and rule values must be readable back by Phase 004 (FR-010, SC-005).

**Scale/Scope**: One rule (`SALES_PRICE_CHANGE_001`), one rules table. Two-to-three deliverable files; optional README touch-up.

## Constitution Check

*GATE: Must pass before Phase 003 implementation. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Free Edition / Serverless Constraints | PASS | All work runs serverless; `config.py` is stdlib-only. No secrets, no external calls. |
| II. Delta CDF Events | PASS (N/A) | This phase does not read CDF or build events; it stores the *configuration* that describes which column to watch. No raw CDF rows are touched. |
| III. Rule-Based Agent (No LLM) | PASS | Stores the deterministic rule thresholds that the Phase 004 agent will read. No LLM, no decision logic executed here. |
| IV. Data Safety & Idempotency | PASS | `MERGE` keyed on `rule_id` (the PK): `WHEN MATCHED THEN UPDATE`, `WHEN NOT MATCHED THEN INSERT`. Re-run leaves exactly one row (SC-001, SC-003). Source table never modified. |
| V. Audit & Observability | PASS | Rule row carries `created_at`/`updated_at`. Notebook displays the active rule and prints an unambiguous status. The rule itself is the configuration that makes every later alert traceable (`rule_id`). |

**Gate result**: PASS. No violations; Complexity Tracking not required.

**Post-design re-check**: PASS — design artifacts add no new dependencies, no new tables, and no external calls; idempotency (keyed on PK `rule_id`) and the serverless-only boundary are preserved.

## Project Structure

### Documentation (this feature)

```text
specs/003-monitoring-rules/
├── plan.md              # This file
├── spec.md              # Feature specification (present)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── agent-rules-merge.md   # Contract for the MERGE upsert (match key, columns, values)
│   └── notebook-contract.md   # Behavioral contract for the setup notebook + validations
└── checklists/
    └── requirements.md  # From /speckit-specify
```

### Source Code (repository root)

```text
src/cdf_agent_monitoring/
└── config.py            # EXTEND: add RULE_NAME, EVENT_TYPE, CONDITION_TYPE,
                         #         NOTIFICATION_TARGET_TYPE, NOTIFICATION_TARGET_VALUE,
                         #         SOURCE_CATALOG/SOURCE_SCHEMA/SOURCE_TABLE_NAME parts.
                         #         REUSE existing: RULE_ID, BUSINESS_KEY_COLUMNS,
                         #         CONTEXT_COLUMNS, WATCHED_COLUMN, thresholds, RULES_TABLE.

sql/
└── 002_create_agent_rules.sql  # KEEP CREATE TABLE IF NOT EXISTS; APPEND canonical MERGE upsert.

notebooks/
└── 03_setup_monitoring_rules.py  # IMPLEMENT: ensure table → MERGE rule → display → validate → SUCCESS/FAILED

README.md                  # OPTIONAL: add a Phase 003 run note if needed
```

**Structure Decision**: Follow the established convention exactly (Phases 000–002). Constants live in `config.py` and are imported by the notebook (notebook adds `src/` to `sys.path`, mirroring notebooks 01/02). The rule values are defined once in `config.py` so Phase 004 can read them as a fallback (FR-010); the *authoritative* copy at runtime is the `agent_rules` row. The notebook reuses the `[RUN]`/`[OK]`, `run_sql`, `sql_string`, and `display(...)` patterns from notebook 02. The existing `notebooks/03_run_rule_based_agent.py` stub is for Phase 004 and is left untouched — Phase 003's notebook is the new `03_setup_monitoring_rules.py`.

## Key Design Decisions (see research.md for full rationale)

- **Rule schema is fixed by the existing table.** The live `agent_rules` table already has the exact 16 columns (verified against `information_schema`). The notebook builds a one-row source (via a temp view / `VALUES`) whose columns match, then `MERGE`s. No schema change.
- **MERGE match key is `rule_id`.** `rule_id` is the table's PK (NOT ENFORCED). Matching on it makes the upsert idempotent and converges any stale row to the canonical values — `WHEN MATCHED THEN UPDATE SET` all business columns + `updated_at = current_timestamp()`, `WHEN NOT MATCHED THEN INSERT` all columns with `created_at = updated_at = current_timestamp()`.
- **Timestamps.** `created_at` is set only on insert; `updated_at` is set on both insert and update — both via `current_timestamp()` so no value is hardcoded.
- **Column-list values stored as comma-separated strings.** `business_key_columns = 'sls_ord_num'`, `context_columns = 'sls_prd_key,sls_cust_id,sls_quantity,sls_sales'` (no spaces) — matching PLAN.md and the existing schema. Python lists in `config.py` are joined with `","` to produce these.
- **`schema_name` is the *source* schema.** Stored value is `bronz` (the monitored table's schema), not the monitoring schema — consistent with PLAN.md/constitution.
- **Validation is assertion-based and explicit.** The notebook runs: (1) table-exists check, (2) `COUNT(*) WHERE rule_id=... AND is_active` must equal 1, (3) field-equality checks for `watched_column`, `business_key_columns`, `medium_threshold_percent=5.0`, `high_threshold_percent=10.0`, source parts, condition type, and notification target. Any failure collects a reason and the notebook prints `FAILED: <reasons>`; all-pass prints `SUCCESS`.
- **Live-workspace grounding (FR-013).** Confirmed pre-implementation: the table exists with 16 expected columns and 0 rows. Phase 003 is only "successful" once the real `agent_rules` table holds exactly one active `SALES_PRICE_CHANGE_001` row, demonstrated via the displayed row.
