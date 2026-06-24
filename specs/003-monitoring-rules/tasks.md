---
description: "Task list for Phase 003 — Monitoring Rules Table"
---

# Tasks: Monitoring Rules Table (Phase 003)

**Input**: Design documents from `specs/003-monitoring-rules/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: No automated test suite is requested for this phase. Validation is performed in-notebook against the live workspace (FR-013) and via `quickstart.md`. No `pytest` tasks are generated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US4)
- All paths are repository-relative.

## Conventions (from plan.md)

- Notebook reuses the `[RUN]`/`[OK]`, `run_sql`, `sql_string`, `display(...)` patterns from `notebooks/02_run_cdf_detection.py`; adds `src/` to `sys.path` to import `cdf_agent_monitoring.config`.
- The notebook `notebooks/03_setup_monitoring_rules.py` is a **single file** built incrementally across US1→US4, so its tasks are sequential (not `[P]` with each other). The SQL file and `config.py` are separate files and parallelizable against the notebook.
- Canonical rule values and the MERGE/validation contracts: see `data-model.md`, `contracts/agent-rules-merge.md`, `contracts/notebook-contract.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working environment before writing code.

- [X] T001 Confirm DEFAULT `.databrickscfg` profile / Databricks MCP server is reachable and serverless compute is available (no code change; grounding for FR-013). Already verified during planning: `agent_rules` exists with 16 columns and 0 rows.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared configuration and table DDL that every later task depends on.

**⚠️ CRITICAL**: Complete before any user-story phase.

- [X] T002 [P] Extend `src/cdf_agent_monitoring/config.py` with the new rule constants (do not change existing ones): `RULE_NAME = "Sales price change monitoring"`, `EVENT_TYPE = "SALES_PRICE_CHANGE"`, `CONDITION_TYPE = "percent_change"`, `NOTIFICATION_TARGET_TYPE = "alert_table"`, `NOTIFICATION_TARGET_VALUE = NOTIFICATION_LOG_TABLE`, `SOURCE_CATALOG = "databricks_arrow_cata"`, `SOURCE_SCHEMA = "bronz"`, `SOURCE_TABLE_NAME = "sales_info"`. Keep `SOURCE_TABLE == f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.{SOURCE_TABLE_NAME}"` consistent. (data-model.md "Config Constants")
- [X] T003 [P] (Task 1) Confirm `sql/002_create_agent_rules.sql` keeps `CREATE TABLE IF NOT EXISTS databricks_arrow_cata.monitoring.agent_rules` with all 16 columns and `PRIMARY KEY (rule_id) NOT ENFORCED`, safe to rerun. File already matches the live schema; add a brief header comment noting it is idempotent. (FR-002)

**Checkpoint**: Constants available to import; table DDL confirmed idempotent.

---

## Phase 3: User Story 1 - Confirm the Rules Table Exists (Priority: P1) 🎯 MVP

**Goal**: Scaffold the Phase 003 notebook and have it confirm `agent_rules` exists before any write.

**Independent Test**: Run the notebook against a workspace where the table exists → it confirms presence and the rule-config columns; against a missing table → it reports the precondition failure and stops.

- [X] T004 [US1] (Task 3 scaffold) Create `notebooks/03_setup_monitoring_rules.py` with the `# Databricks notebook source` header, print `Phase 003 - Setup Monitoring Rules` and key constants (`RULES_TABLE`, `RULE_ID`, source table, thresholds), and the serverless/no-CDF/no-source-write banner. Add `src/` to `sys.path` and `from cdf_agent_monitoring import config`. Include the `run_sql`/`sql_string` helpers (mirror notebook 02). (contracts/notebook-contract.md stages 1–2)
- [X] T005 [US1] (Task 3 ensure-table) In `notebooks/03_setup_monitoring_rules.py`, add the "ensure table exists" stage: run `CREATE TABLE IF NOT EXISTS ... agent_rules (...)` (same 16-column DDL as `sql/002_create_agent_rules.sql`) and verify the table is present; raise a clear `RuntimeError` if it cannot be confirmed/created. (FR-001, contracts/notebook-contract.md stage 3, V1)

**Checkpoint**: Notebook runs through table confirmation and fails fast if the table is missing.

---

## Phase 4: User Story 2 - Upsert the First Rule Idempotently (Priority: P1)

**Goal**: Insert `SALES_PRICE_CHANGE_001` once via `MERGE` keyed on `rule_id`; re-runs never duplicate.

**Independent Test**: Run the upsert twice → exactly one row for `SALES_PRICE_CHANGE_001` after both runs.

- [X] T006 [P] [US2] (Task 2) Append the canonical idempotent `MERGE INTO databricks_arrow_cata.monitoring.agent_rules` for `SALES_PRICE_CHANGE_001` to `sql/002_create_agent_rules.sql` — match on `rule_id`, `WHEN MATCHED THEN UPDATE SET` business columns + `updated_at = current_timestamp()`, `WHEN NOT MATCHED THEN INSERT` all columns with `created_at`/`updated_at = current_timestamp()`. (FR-003, contracts/agent-rules-merge.md)
- [X] T007 [US2] (Task 4) In `notebooks/03_setup_monitoring_rules.py`, define the 14 business-column rule values from `config.py`, joining list constants into comma-separated strings (`business_key_columns = "sls_ord_num"`, `context_columns = "sls_prd_key,sls_cust_id,sls_quantity,sls_sales"`). Build a one-row source (temp view or `VALUES`). (FR-004, FR-010, data-model.md entity 2)
- [X] T008 [US2] (Task 5) In `notebooks/03_setup_monitoring_rules.py`, execute the `MERGE` upsert against the one-row source (same semantics as T006); report before/after counts and inserted-vs-updated for `SALES_PRICE_CHANGE_001`. (FR-003, FR-005, contracts/agent-rules-merge.md, SC-001/SC-003)

**Checkpoint**: After running, exactly one row exists for `SALES_PRICE_CHANGE_001`; re-running keeps it at one.

---

## Phase 5: User Story 3 - Validate the Stored Rule (Priority: P1)

**Goal**: Prove the persisted rule is unique, active, and matches the expected source table and columns.

**Independent Test**: Read back the row → exactly one active rule; every checked field equals its canonical value; a deliberately wrong value yields a FAILED reason.

- [X] T009 [US3] (Task 6) In `notebooks/03_setup_monitoring_rules.py`, add the "exactly one active rule" check: `COUNT(*) WHERE rule_id = 'SALES_PRICE_CHANGE_001' AND is_active = true` must equal 1; collect a clear failure reason (e.g., `expected 1 active rule, found <n>`) if 0 or >1. (FR-006, V2/V3, SC-001)
- [X] T010 [US3] (Task 7) In `notebooks/03_setup_monitoring_rules.py`, add field-equality checks V4–V11 against the stored row: `watched_column = sls_price`, `business_key_columns = sls_ord_num`, `context_columns = sls_prd_key,sls_cust_id,sls_quantity,sls_sales`, `medium_threshold_percent = 5.0`, `high_threshold_percent = 10.0`, `catalog/schema/table` resolve to `databricks_arrow_cata.bronz.sales_info`, `condition_type = percent_change`, notification target `alert_table` / `databricks_arrow_cata.monitoring.notification_log`. Accumulate all failure reasons. (FR-007, V4–V11, SC-002)

**Checkpoint**: Validation accumulates a complete list of any mismatches in one run.

---

## Phase 6: User Story 4 - Display the Rule and Print Status (Priority: P2)

**Goal**: Show the active rule and emit one unambiguous SUCCESS/FAILED line.

**Independent Test**: Run notebook → it displays the `SALES_PRICE_CHANGE_001` row and prints exactly one terminal status reflecting the validation result.

- [X] T011 [US4] (Task 8) In `notebooks/03_setup_monitoring_rules.py`, `display()` the active rule row(s) `WHERE rule_id = 'SALES_PRICE_CHANGE_001' AND is_active = true` with the key columns. (FR-008, contracts/notebook-contract.md stage 5)
- [X] T012 [US4] In `notebooks/03_setup_monitoring_rules.py`, print exactly one terminal status: `SUCCESS: SALES_PRICE_CHANGE_001 is active with the expected configuration.` when zero failures, else `FAILED: <semicolon-separated reasons>` from T009/T010. (FR-009, SC-004, contracts/notebook-contract.md "Output contract")

**Checkpoint**: Notebook always ends with a single SUCCESS or FAILED line.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and live-workspace validation.

- [X] T013 [P] (Task 9) Add a concise Phase 003 run note to `README.md` (how to run `notebooks/03_setup_monitoring_rules.py` and the expected SUCCESS output). Do not document future-phase implementation. (Required Files, out-of-scope guard)
- [X] T014 Execute `quickstart.md` against the live Databricks workspace (DEFAULT profile / MCP server): run the notebook, confirm first run inserts 1 row and prints SUCCESS, re-run keeps count at 1 and prints SUCCESS; capture the displayed active row as evidence. Phase 003 is not successful until this passes (FR-013, SC-006).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all user stories (constants + DDL).
- **User Stories (Phases 3–6)**: Depend on Foundational. Because they all edit the single notebook file, run them **in order US1 → US2 → US3 → US4** (the notebook is built incrementally).
- **Polish (Phase 7)**: Depends on all user stories complete; T014 is the final live-validation gate.

### Story Dependencies

- **US1 (P1)**: Foundational only. MVP scaffold + table confirmation.
- **US2 (P1)**: Needs US1 notebook scaffold (same file) + T002 constants + (optionally) T006 SQL reference.
- **US3 (P1)**: Needs US2 (a row must exist to validate).
- **US4 (P2)**: Needs US3 (status reflects validation results).

### Within the notebook

- Header/helpers (T004) → ensure-table (T005) → constants (T007) → MERGE (T008) → validations (T009, T010) → display (T011) → status (T012).

### Parallel Opportunities

- **T002** (config.py) and **T003** (SQL DDL) — different files, run in parallel.
- **T006** (SQL MERGE, separate file) can be written in parallel with the US2 notebook tasks.
- **T013** (README) can be written any time after US4 in parallel with T014 prep.
- Notebook tasks (T004–T012) are **sequential** (same file) — not parallel.

---

## Parallel Example: Foundational Phase

```bash
# These two touch different files and have no interdependency:
Task: "T002 Extend src/cdf_agent_monitoring/config.py with new rule constants"
Task: "T003 Confirm sql/002_create_agent_rules.sql DDL is idempotent"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Phase 1 Setup → Phase 2 Foundational (constants + DDL).
2. US1: scaffold notebook, confirm table.
3. US2: define constants, MERGE the rule.
4. **STOP and VALIDATE**: one active row exists for `SALES_PRICE_CHANGE_001`. This already satisfies the phase's core expected output.

### Incremental Delivery

1. Foundation ready (T001–T003).
2. + US1 → notebook confirms table.
3. + US2 → rule upserted idempotently (MVP outcome).
4. + US3 → values validated.
5. + US4 → display + SUCCESS/FAILED.
6. + Polish → README + live quickstart validation (T014 gate).

---

## Notes

- Out of scope (do not implement): reading CDF, updating the source table, creating events, running agent/severity logic, creating alerts or notification-log rows, Genie, external notifications.
- The existing `notebooks/03_run_rule_based_agent.py` stub belongs to Phase 004 — leave it untouched.
- Idempotency keyed on `rule_id` (PK). Re-running the notebook must keep exactly one row (SC-003).
- `[P]` = different files, no dependency. Notebook = single file = sequential.
