# Phase 1 Data Model: Enable and Validate Change Data Feed

**Feature**: Phase 001 — Enable and Validate CDF
**Date**: 2026-06-23

This phase creates **no new tables**. It toggles one table property, performs one test UPDATE, and reads CDF change records. The "entities" below are the data shapes the notebook works with — not persisted monitoring tables (those belong to later phases).

---

## E1. Source Table (subject of the change)

**Name**: `databricks_arrow_cata.bronz.sales_info`
**Type**: Existing managed Delta table (created/confirmed in Phase 000). Read, one ALTER, one UPDATE.

Columns relevant to this phase:

| Column | Role | Notes |
|--------|------|-------|
| `sls_ord_num` | Business key | Filter for the test order `SO43697`. |
| `sls_price` | Watched column | Multiplied by 1.15 in the test update. Numeric. |
| `sls_prd_key`, `sls_cust_id`, `sls_quantity`, `sls_sales` | Context | Displayed for human readability; not modified. |

Property toggled:

| Property | Before | After |
|----------|--------|-------|
| `delta.enableChangeDataFeed` | `false` / unset (per Phase 000) | `true` |

**Validation rules**:
- Table MUST exist and be Delta before any modification (FR-001). Format checked via `DESCRIBE DETAIL` → `format = 'delta'`.
- The UPDATE MUST match exactly one row (`sls_ord_num = 'SO43697'`); zero matches → warning + FAILED (FR-009).

---

## E2. Baseline Version

**Shape**: A single non-negative integer (`baseline_version`) held in a Python variable during the notebook run.

| Field | Type | Source |
|-------|------|--------|
| `baseline_version` | LONG | Top row `version` from `DESCRIBE HISTORY <table> LIMIT 1`, captured **after** CDF enablement and **before** the UPDATE. |

**Validation rules**:
- MUST be captured before the UPDATE (FR-006).
- The UPDATE's resulting commit version MUST be strictly greater than `baseline_version`.

---

## E3. Test Row Snapshot (before / after)

**Shape**: Two in-memory readings of the target order's row.

| Field | Type | When | Notes |
|-------|------|------|-------|
| `old_price` | numeric | Before UPDATE | Read from `sls_price WHERE sls_ord_num='SO43697'`. |
| `new_price` | numeric | After UPDATE | Expected ≈ `old_price * 1.15`. |
| `num_affected_rows` | LONG | UPDATE result | Expected `1`. |

**Validation rules**:
- `new_price ≈ old_price * 1.15` within rounding tolerance (SC-005).
- `num_affected_rows == 1` (SC-003).

---

## E4. Change Records (`table_changes()` output)

**Shape**: Rows returned by `table_changes('databricks_arrow_cata.bronz.sales_info', baseline_version)` filtered to `sls_ord_num = 'SO43697'`.

CDF metadata columns (added to the table's normal columns):

| Column | Type | Notes |
|--------|------|-------|
| `_change_type` | STRING | One of `update_preimage`, `update_postimage`, `insert`, `delete`. For this phase the UPDATE yields a matched `update_preimage` + `update_postimage` pair. |
| `_commit_version` | LONG | Version of the commit that produced the change (the UPDATE's version). |
| `_commit_timestamp` | TIMESTAMP | When the commit occurred. |

**Derived values for the result**:
- `cdf_old_price` = `sls_price` of the `update_preimage` row.
- `cdf_new_price` = `sls_price` of the `update_postimage` row.
- `change_commit_version` = `_commit_version` of that pair.

**Validation rules** (drive PASS/FAIL):
- At least one `update_preimage` row present (FR-011).
- At least one `update_postimage` row present (FR-011).
- `cdf_old_price` matches the pre-update `old_price`; `cdf_new_price` matches the post-update `new_price` (corroboration).

---

## E5. Validation Result (phase outcome)

**Shape**: The console-printed summary; not persisted.

| Field | Type | Notes |
|-------|------|-------|
| `validation_status` | STRING | `SUCCESS` only if both pre-image and post-image are present; else `FAILED`. |
| `old_price` | numeric | Displayed. |
| `new_price` | numeric | Displayed. |
| `change_commit_version` | LONG | Displayed. |
| `reason` | STRING | On FAILED, explains what was missing. |
| `rollback_sql` | STRING | Printed suggestion; never auto-executed. |

**State transition**: `STARTED → (preconditions ok) → CDF enabled → baseline captured → updated → changes read → SUCCESS | FAILED`. Any precondition failure (table missing/not Delta, order absent) short-circuits to a clear error/FAILED before later steps.
