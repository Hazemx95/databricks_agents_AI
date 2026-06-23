---
description: "Task list for Phase 001 — Enable and Validate Change Data Feed"
---

# Tasks: Enable and Validate Change Data Feed (Phase 001)

**Input**: Design documents from `specs/001-enable-cdf/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/notebook-contract.md, quickstart.md

**Tests**: No automated test tasks. This phase is validated by the notebook's own self-checks and the `quickstart.md` manual run (no `tests/` suite requested).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different file, no dependency on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)
- All paths are repo-root-relative.

## Scope Guardrails (apply to EVERY task)

- Touch ONLY: `sql/007_enable_cdf.sql`, `notebooks/01_enable_cdf_and_validate.py`, `src/cdf_agent_monitoring/config.py` (constants), and `README.md` (execution notes only).
- Serverless only. No secrets, no external network/API calls, no LangChain/OpenAI/RAG.
- DO NOT create event JSON, write `change_events`/`agent_alerts`/`notification_log`/`agent_run_log` rows, build Genie context, or send any external notification.
- DO NOT auto-execute the rollback.

---

## Phase 1: Setup (Shared)

**Purpose**: Centralize the Phase 001 constants so the notebook stays consistent with project convention.

- [ ] T001 [P] Add Phase 001 constants to `src/cdf_agent_monitoring/config.py`: `TEST_ORDER_NUMBER = "SO43697"` and `PRICE_MULTIPLIER = 1.15` (reuse existing `SOURCE_TABLE`, `WATCHED_COLUMN`, `BUSINESS_KEY_COLUMNS`). Do not remove or rename existing constants.

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Notebook scaffold that every later step builds on. Must complete before any US1–US3 notebook step.

**⚠️ CRITICAL**: All notebook tasks below edit the single file `notebooks/01_enable_cdf_and_validate.py`, so they are inherently **sequential** (no `[P]`), and the stories run in order US1 → US2 → US3 (CDF must be enabled before baseline capture; baseline before the update).

- [ ] T002 Rewrite the stub `notebooks/01_enable_cdf_and_validate.py` with the Databricks notebook header (`# Databricks notebook source`), a clear "Phase 001 — Enable and Validate Change Data Feed" title comment, the `sys.path` insertion of `src/` and `from cdf_agent_monitoring import config` pattern (as in `notebooks/00_project_bootstrap.py`), local constants `SOURCE_TABLE`, `TEST_ORDER_NUMBER = "SO43697"`, `WATCHED_COLUMN = "sls_price"`, and a `run_sql(label, sql_text)` helper. Print the constants at start. Remove the obsolete `phase001/sql/` references from the old stub. (US-shared scaffold; satisfies "notebook header/constants" required task)

**Checkpoint**: Notebook opens on serverless, loads config, prints constants.

---

## Phase 3: User Story 1 - Enable Change Data Feed on Source Table (Priority: P1) 🎯 MVP

**Goal**: Confirm the table is Delta, report current CDF status, and idempotently enable CDF.

**Independent Test**: Run the notebook through this phase; `delta.enableChangeDataFeed` reads `true` afterward and the table data/schema is unchanged. Re-running does not error.

- [ ] T003 [P] [US1] Write `sql/007_enable_cdf.sql`: a leading comment marking it **Phase 001**, then `ALTER TABLE databricks_arrow_cata.bronz.sales_info SET TBLPROPERTIES (delta.enableChangeDataFeed = true);`. Must be idempotent and must NOT drop/recreate or alter schema/data. (Required task: "Update CDF SQL script")
- [ ] T004 [US1] In `notebooks/01_enable_cdf_and_validate.py`, add a precondition step that runs `DESCRIBE DETAIL` and `SHOW TBLPROPERTIES` on `SOURCE_TABLE`, displays table format and properties, and asserts/stops with a clear message if `format != 'delta'`. (Required task: "Validate source table"; FR-001, FR-002)
- [ ] T005 [US1] In the notebook, read current `delta.enableChangeDataFeed`; if not `true`, execute `sql/007_enable_cdf.sql` via `run_sql`; then re-read and display the final CDF status. Idempotent (no error when already enabled). (Required task: "Enable CDF safely"; FR-003, FR-004, FR-005)

**Checkpoint**: CDF enabled and confirmed `true`; safe to re-run.

---

## Phase 4: User Story 2 - Capture Baseline Version Before Test Update (Priority: P1)

**Goal**: Record the table's current commit version before any modification, so `table_changes()` reads from a precise, reproducible point.

**Independent Test**: After this phase, `baseline_version` is printed as a non-negative integer, captured after CDF enablement and strictly before the update.

**Depends on**: US1 complete (CDF must be enabled first).

- [ ] T006 [US2] In the notebook, run `DESCRIBE HISTORY SOURCE_TABLE LIMIT 1` (top row `version`), store it as `baseline_version`, and print it. Must occur after CDF enable (T005) and before the update (T008). (Required task: "Capture baseline version"; FR-006)

**Checkpoint**: `baseline_version` captured and printed before any data change.

---

## Phase 5: User Story 3 - Apply Safe Test Update and Validate CDF Records (Priority: P1)

**Goal**: Apply the controlled +15% price update to `SO43697`, then prove CDF captured both old and new values via `table_changes()`.

**Independent Test**: Update affects exactly 1 row; `table_changes()` from baseline shows one `update_preimage` and one `update_postimage` for `SO43697`; final line prints `SUCCESS` with old price, new price, and commit version.

**Depends on**: US2 complete (`baseline_version` must exist before the update).

- [ ] T007 [US3] In the notebook, read the `SO43697` row (key column `sls_ord_num`) **before** the update, store `old_price` from `sls_price`, and display the row. If zero rows match, print a clear warning and mark the run FAILED. (Required task: "Capture old test row"; FR-009, FR-012)
- [ ] T008 [US3] In the notebook, run `UPDATE databricks_arrow_cata.bronz.sales_info SET sls_price = sls_price * 1.15 WHERE sls_ord_num = 'SO43697';`, capture `num_affected_rows`, and warn if not exactly 1. (Required task: "Run controlled update"; FR-007, FR-008, FR-009)
- [ ] T009 [US3] In the notebook, re-read the `SO43697` row **after** the update, store `new_price`, and display the row. (Required task: "Capture new test row"; FR-012)
- [ ] T010 [US3] In the notebook, query `table_changes('databricks_arrow_cata.bronz.sales_info', baseline_version)` filtered to `sls_ord_num = 'SO43697'`, ordered by `_commit_version, _change_type`, and display the change rows. (Required task: "Validate CDF rows"; FR-010)
- [ ] T011 [US3] In the notebook, assert presence of both an `update_preimage` row and an `update_postimage` row; extract `cdf_old_price`, `cdf_new_price`, and `change_commit_version`. Print `SUCCESS` only when both images exist, else `FAILED` with the reason; print `old_price`, `new_price`, and `change_commit_version`. (Required tasks: "Validate CDF rows" + "Print validation result"; FR-011, FR-013, FR-014)
- [ ] T012 [US3] In the notebook, print a ready-to-paste rollback suggestion (`UPDATE ... SET sls_price = sls_price / 1.15 WHERE sls_ord_num = 'SO43697';`) with a note that it is NOT executed automatically. Do not run it. (Required task: "Print rollback SQL suggestion")

**Checkpoint**: End-to-end CDF validation prints a clear PASS/FAIL with old/new price, commit version, and a manual rollback suggestion.

---

## Phase 6: Polish & Validation

**Purpose**: Confirm the full run and capture execution notes if needed.

- [ ] T013 Run `quickstart.md` end-to-end on serverless and confirm all Pass Criteria (SC-001…SC-008), including idempotent re-run of the enable step.
- [ ] T014 [P] If execution notes are needed, add a short "Phase 001 — Enable & Validate CDF" run section to `README.md` (how to run the notebook, that it mutates `SO43697` by +15%, and that rollback is manual). Skip if existing docs already cover it.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: After Setup — blocks all story phases.
- **US1 (Phase 3)**: After Foundational.
- **US2 (Phase 4)**: After US1 — CDF must be enabled before baseline capture.
- **US3 (Phase 5)**: After US2 — `baseline_version` must exist before the update.
- **Polish (Phase 6)**: After US3.

> Unlike a typical multi-story feature, the three stories here form a **linear pipeline** (enable → baseline → update/validate) and are not independently runnable out of order. Each phase is still an independently *verifiable* checkpoint.

### Within the notebook

- All notebook tasks (T002, T004–T012) edit the same file and must be applied in listed order; none are `[P]`.

### Parallel Opportunities

- T001 (config.py) and T003 (`sql/007_enable_cdf.sql`) are separate files with no interdependency → can run in parallel, and both before/alongside the notebook scaffold (T003 is consumed by T005).
- T014 (README) is independent of notebook internals → `[P]` at the end.

---

## Parallel Example

```bash
# Independent files, can be done together up front:
Task T001: "Add Phase 001 constants to src/cdf_agent_monitoring/config.py"
Task T003: "Write sql/007_enable_cdf.sql (Phase 001 CDF enablement)"
```

---

## Implementation Strategy

### MVP scope

The whole phase is the MVP — but the smallest demonstrable increment is **US1 (Phase 3)**: CDF enabled and confirmed `true`. US2 + US3 then prove it captures changes. Recommended path:

1. Phase 1 Setup (T001) + write SQL (T003).
2. Phase 2 scaffold (T002).
3. Phase 3 US1 (T004–T005) → confirm CDF `true`.
4. Phase 4 US2 (T006) → baseline printed.
5. Phase 5 US3 (T007–T012) → SUCCESS/FAILED + rollback suggestion.
6. Phase 6 (T013–T014) → quickstart validation + optional README note.

---

## Notes

- `[P]` = different file, no dependency.
- Honors explicit out-of-scope: no event JSON, no monitoring-table writes, no Genie, no external notification.
- The test UPDATE is intentionally non-idempotent (each run adds +15%); capture/inspect within a single run and use the printed rollback to revert manually.
- Commit after each logical group; stop at any checkpoint to validate independently.
