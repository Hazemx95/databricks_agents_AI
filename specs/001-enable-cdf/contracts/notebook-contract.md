# Contract: CDF Enablement SQL + Validation Notebook

**Feature**: Phase 001 — Enable and Validate CDF
**Date**: 2026-06-23

This phase exposes two interfaces: a SQL script and a Databricks notebook. Below are their behavioral contracts — inputs, ordered steps, outputs, and failure modes. Implementation bodies belong to `tasks.md` / the implementation phase, not here.

---

## Contract A: `sql/007_enable_cdf.sql`

**Purpose**: Idempotently enable Delta CDF on the source table.

**Contract**:
- Contains a single effective statement:
  ```sql
  ALTER TABLE databricks_arrow_cata.bronz.sales_info
  SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
  ```
- MUST be safe to run repeatedly (no-op when already enabled; never errors on re-run).
- MUST NOT drop, recreate, or alter the schema/data of the table.
- MAY include a leading comment block describing intent (Phase 001, serverless, idempotent).

**Postcondition**: `SHOW TBLPROPERTIES databricks_arrow_cata.bronz.sales_info` reports `delta.enableChangeDataFeed = true`.

---

## Contract B: `notebooks/01_enable_cdf_and_validate.py`

**Purpose**: Run the full enable-and-validate sequence on serverless compute and report a clear status.

**Inputs** (from `src/cdf_agent_monitoring/config.py`):
- `SOURCE_TABLE = "databricks_arrow_cata.bronz.sales_info"`
- `BUSINESS_KEY_COLUMNS` (uses `sls_ord_num`), `WATCHED_COLUMN = "sls_price"`
- `TEST_ORDER_NUM = "SO43697"` (NEW)
- `PRICE_MULTIPLIER = 1.15` (NEW)

**Ordered steps** (this order is mandatory — CDF only records commits made after enablement):

| # | Step | Behavior | Maps to |
|---|------|----------|---------|
| 1 | Load config | Add `src/` to `sys.path`; import `config`. Print key constants. | — |
| 2 | Precondition: table exists & is Delta | `DESCRIBE DETAIL`; assert `format == 'delta'`. On failure: print clear error, stop. | FR-001 |
| 3 | Check current CDF status | Read `delta.enableChangeDataFeed` via `SHOW TBLPROPERTIES`; print before-state. | FR-002 |
| 4 | Enable CDF | Run `sql/007_enable_cdf.sql` (idempotent). Confirm property now `true`. | FR-003, FR-004, FR-005 |
| 5 | Capture baseline version | `DESCRIBE HISTORY ... LIMIT 1` → `baseline_version`; print it. **Before** the update. | FR-006 |
| 6 | Read test row before | Select the `SO43697` row; store `old_price`; display row. If order absent → warn, mark FAILED, stop. | FR-009, edge case |
| 7 | Run safe update | `UPDATE ... SET sls_price = sls_price * 1.15 WHERE sls_ord_num = 'SO43697'`. Capture `num_affected_rows`; warn if `0`. | FR-007, FR-008, FR-009 |
| 8 | Read test row after | Re-select the row; store `new_price`; display row. | FR-012 |
| 9 | Query changes | `table_changes(SOURCE_TABLE, baseline_version)` filtered to `SO43697`; display the change rows ordered by `_commit_version, _change_type`. | FR-010 |
| 10 | Validate pre/post image | Assert `update_preimage` present AND `update_postimage` present; extract `cdf_old_price`, `cdf_new_price`, `change_commit_version`. | FR-011, FR-012 |
| 11 | Print status | Print `old_price`, `new_price`, `change_commit_version`, and `SUCCESS` (both images present) or `FAILED` (+reason). | FR-013, FR-014 |
| 12 | Print rollback suggestion | Print `UPDATE ... SET sls_price = sls_price / 1.15 WHERE sls_ord_num = 'SO43697';` and a note that it is NOT executed automatically. | scope |

**Outputs** (console only — no table writes):
- Before/after CDF status, baseline version, before/after rows, the CDF change rows, and the final `SUCCESS`/`FAILED` line with old price, new price, and commit version.
- Rollback SQL suggestion (printed, never executed).

**Failure modes**:
- Table missing / not Delta → clear error, stop before any mutation (step 2).
- Order `SO43697` absent → warning, `FAILED`, stop before/at update (step 6/7).
- `table_changes()` returns no matched pre/post image → `FAILED` with reason (step 10/11).

**Invariants / guardrails**:
- MUST run on serverless only; no external network calls, no secrets.
- MUST NOT write to any monitoring table, build event JSON, or send notifications.
- MUST NOT auto-execute the rollback.
- MUST capture baseline strictly before the update so re-runs stay internally consistent.
