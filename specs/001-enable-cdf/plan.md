# Implementation Plan: Enable and Validate Change Data Feed (Phase 001)

**Branch**: `feature/001-enable-cdf` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-enable-cdf/spec.md`

## Summary

Enable Delta Change Data Feed (CDF) on `databricks_arrow_cata.bronz.sales_info`, then prove it works by applying one controlled +15% price update to order `SO43697` and confirming `table_changes()` returns matched `update_preimage` / `update_postimage` rows. Delivery is two artifacts: an idempotent SQL script `sql/007_enable_cdf.sql` (the `ALTER TABLE ... SET TBLPROPERTIES` enablement) and a self-contained validation notebook `notebooks/01_enable_cdf_and_validate.py` that runs the full check→enable→baseline→update→validate→status sequence on serverless compute, prints a clear PASS/FAIL status, and prints (but never auto-runs) a rollback SQL suggestion. No monitoring tables are written; this is purely a CDF enablement-and-validation harness.

## Technical Context

**Language/Version**: Python 3.12 (Databricks notebook source) + Spark SQL (Delta Lake)

**Primary Dependencies**: Databricks serverless Spark runtime; Delta Lake CDF (`delta.enableChangeDataFeed`, `table_changes()`); project `src/cdf_agent_monitoring/config.py` for shared constants. No external Python packages (no LangChain / OpenAI / RAG).

**Storage**: Source Delta table `databricks_arrow_cata.bronz.sales_info` (read + one test UPDATE + one ALTER). No monitoring tables read or written in this phase.

**Testing**: Manual + self-validating notebook. The notebook asserts pre-image/post-image presence and prints `SUCCESS`/`FAILED`; `quickstart.md` documents the runnable validation scenario and expected output.

**Target Platform**: Databricks Free Edition, serverless compute only.

**Project Type**: Databricks data-engineering project (SQL scripts in `sql/`, notebooks in `notebooks/`, shared Python package in `src/cdf_agent_monitoring/`).

**Performance Goals**: Not performance-sensitive. Single-row UPDATE on one order; validation reads a tiny CDF window. Whole notebook completes in seconds-to-minutes on serverless.

**Constraints**: Serverless only; no classic clusters; no hardcoded secrets; no external network calls. The test UPDATE intentionally mutates the bronze source table (the only phase that does so) — must be clearly logged and accompanied by a printed rollback suggestion.

**Scale/Scope**: One table, one order (`SO43697`), one watched column (`sls_price`). Two deliverable files plus extension of `config.py` with Phase 001 constants.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Free Edition / Serverless Constraints | PASS | All work runs on serverless Spark SQL; no classic clusters, secrets, or external APIs. |
| II. Delta CDF Events | PASS | This phase *enables* the CDF mechanism that every later event depends on. No structured JSON events yet (correctly deferred to Phase 002). |
| III. Rule-Based Agent (No LLM) | PASS (N/A) | No agent logic in this phase; no LLM. |
| IV. Data Safety & Idempotency | PARTIAL — justified | The `ALTER TABLE` enablement *is* idempotent. The test UPDATE is **not** idempotent (re-running applies a further +15%). This is inherent to validating CDF with a real write. Mitigations below; see Complexity Tracking. |
| V. Audit & Observability | PARTIAL — justified | Per the explicit phase scope, output is console-only (clear `[RUN]`/`[OK]` logging + PASS/FAIL). Writing to `agent_run_log` is intentionally deferred; see Complexity Tracking. |

**Gate result**: PASS with two justified partials documented in Complexity Tracking. No unjustified violations.

**Post-design re-check**: PASS — design artifacts (research.md, data-model.md, contracts/notebook-contract.md, quickstart.md) introduce no new dependencies, tables, or external calls and preserve both mitigations.

## Project Structure

### Documentation (this feature)

```text
specs/001-enable-cdf/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification (already present)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── notebook-contract.md   # Phase 1 output: behavioral contract for SQL + notebook
└── checklists/
    └── requirements.md  # From /speckit-specify
```

### Source Code (repository root)

```text
sql/
└── 007_enable_cdf.sql                  # NEW: idempotent CDF enablement (ALTER TABLE SET TBLPROPERTIES)

notebooks/
└── 01_enable_cdf_and_validate.py       # REWRITE: full check→enable→baseline→update→validate→status flow

src/cdf_agent_monitoring/
└── config.py                           # EXTEND: add Phase 001 constants (TEST_ORDER_NUM, PRICE_MULTIPLIER, etc.)
```

**Structure Decision**: Follow the Phase 000 convention exactly: SQL scripts live in `sql/` with a numbered prefix (`007_...` continues the existing `000`–`006` sequence), notebooks in `notebooks/`, and shared constants in `src/cdf_agent_monitoring/config.py` (loaded by adding `src/` to `sys.path`, as `notebooks/00_project_bootstrap.py` already does). The current `notebooks/01_enable_cdf_and_validate.py` stub references a non-existent `phase001/sql/` directory and a missing `007_enable_cdf.sql`; it will be **rewritten** to match the Phase 000 layout rather than introducing a divergent `phase001/` tree.

## Complexity Tracking

> Two constitution principles are partially relaxed for this phase. Both are inherent to the phase's purpose, explicitly bounded by the spec, and justified below.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Test UPDATE is not idempotent (re-run applies another +15%) | Validating that CDF captures a real row-level change requires an actual write that produces a new commit version. | A "read-only" validation cannot prove CDF emits `update_preimage`/`update_postimage`. Mitigations: (a) the notebook captures baseline strictly before the update and reads `table_changes()` from that baseline, so each run is internally consistent regardless of prior runs; (b) the notebook prints an exact rollback SQL suggestion but never auto-runs it; (c) the update is scoped to exactly one order. |
| No `agent_run_log` write (console-only audit) | The phase scope explicitly limits output to printed status and forbids writing to monitoring tables; the run-log writer belongs to the agent workflow phases (004+). | Writing to `agent_run_log` now would couple a pure validation harness to the monitoring schema and risk implying the end-to-end workflow exists. Console `[RUN]`/`[OK]`/PASS-FAIL logging preserves observability for this phase without that coupling. |
