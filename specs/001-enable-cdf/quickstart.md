# Quickstart: Enable and Validate Change Data Feed (Phase 001)

**Feature**: Phase 001 — Enable and Validate CDF
**Date**: 2026-06-23

This guide validates that CDF is enabled on the source table and that a price change produces matched pre-image / post-image change records. See [contracts/notebook-contract.md](./contracts/notebook-contract.md) for the full step contract and [data-model.md](./data-model.md) for the data shapes.

---

## Prerequisites

- Phase 000 complete: `databricks_arrow_cata.bronz.sales_info` exists, is Delta, and order `SO43697` is present with a non-null `sls_price`.
- Databricks Free Edition workspace with **serverless** compute.
- `ALTER` + `UPDATE` permission on the source table.
- Repo files available in the workspace: `sql/007_enable_cdf.sql`, `notebooks/01_enable_cdf_and_validate.py`, `src/cdf_agent_monitoring/config.py`.

---

## Run

1. Open `notebooks/01_enable_cdf_and_validate.py` in Databricks and attach serverless compute.
2. Run all cells, top to bottom.

The notebook performs, in order: check table is Delta → report current CDF status → enable CDF (idempotent) → capture baseline version → read the `SO43697` row (old price) → apply `sls_price * 1.15` → read the row again (new price) → read `table_changes()` from the baseline → validate pre/post image → print status + rollback suggestion.

---

## Expected outcome

A successful run prints (values illustrative):

```text
[CDF] delta.enableChangeDataFeed before = false
[CDF] delta.enableChangeDataFeed after  = true
[BASELINE] baseline_version = 7
[BEFORE] SO43697 sls_price = 3578.0
[UPDATE] num_affected_rows = 1
[AFTER]  SO43697 sls_price = 4114.70
[CDF CHANGES] SO43697:
  _change_type=update_preimage   sls_price=3578.0   _commit_version=8
  _change_type=update_postimage  sls_price=4114.70  _commit_version=8
[RESULT] old_price=3578.0  new_price=4114.70  commit_version=8  status=SUCCESS
[ROLLBACK SUGGESTION] (not executed):
  UPDATE databricks_arrow_cata.bronz.sales_info
  SET sls_price = sls_price / 1.15
  WHERE sls_ord_num = 'SO43697';
```

---

## Pass criteria (maps to spec Success Criteria)

- [ ] `delta.enableChangeDataFeed` reads `true` after the run (SC-001).
- [ ] Baseline version printed before the update (SC-002).
- [ ] `num_affected_rows == 1` for the test update (SC-003).
- [ ] `table_changes()` shows exactly one `update_preimage` and one `update_postimage` for `SO43697` (SC-004).
- [ ] `new_price ≈ old_price × 1.15` (SC-005).
- [ ] Final line reads `status=SUCCESS` (SC-006).
- [ ] Re-running the enable step does not error and does not change data/schema (SC-007).
- [ ] No rows written to any monitoring table; no external notification (SC-008).

---

## Failure handling

| Symptom | Meaning | Action |
|---------|---------|--------|
| Error at "check Delta" step | Table missing or not Delta | Re-run Phase 000; confirm catalog/schema/table name. |
| `num_affected_rows = 0` + warning | Order `SO43697` not found | Pick an existing order or restore the row; status will be `FAILED`. |
| `status=FAILED`, no pre/post image | CDF not capturing, or baseline captured after the update | Confirm CDF enabled before baseline; re-run notebook top-to-bottom. |

---

## Cleanup (optional, manual)

The notebook leaves the +15% change in place and does **not** auto-rollback. To revert manually, run the printed rollback suggestion. Note: each enable/validate re-run applies a further +15%, so capture/inspect within a single run.
