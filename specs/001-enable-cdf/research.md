# Phase 0 Research: Enable and Validate Change Data Feed

**Feature**: Phase 001 — Enable and Validate CDF
**Date**: 2026-06-23

The Technical Context had no open `NEEDS CLARIFICATION` markers; the spec and PLAN.md fully constrain the approach. The research below records the key technical decisions and the alternatives weighed.

---

## Decision 1: How to enable CDF idempotently

**Decision**: Use `ALTER TABLE databricks_arrow_cata.bronz.sales_info SET TBLPROPERTIES (delta.enableChangeDataFeed = true);` in `sql/007_enable_cdf.sql`. The notebook first reads `SHOW TBLPROPERTIES` (or `DESCRIBE DETAIL`) to report current status, then runs the ALTER.

**Rationale**: `SET TBLPROPERTIES` to `true` is naturally idempotent — re-applying it when already enabled is a no-op that does not error and does not rewrite data. Reporting status first satisfies FR-002 ("check and report current CDF status before enabling").

**Alternatives considered**:
- *Conditional ALTER (only if not enabled)*: Adds branching logic for no safety gain, since the ALTER is already idempotent. Rejected to keep the SQL declarative; the notebook still reports the before-state for visibility.
- *Set CDF at table creation*: Not applicable — the table already exists (Phase 000) and must not be recreated.

---

## Decision 2: Capturing the baseline version before the update

**Decision**: Capture the current version via `DESCRIBE HISTORY <table> LIMIT 1` (the top row's `version`) — equivalently the max version — and store it in a Python variable **before** running the UPDATE. Read changes with `table_changes('<table>', <baseline_version>)`.

**Rationale**: `table_changes(table, startingVersion)` returns changes from `startingVersion` (inclusive) onward. Capturing the version that exists immediately after CDF is enabled and before the UPDATE guarantees the UPDATE's commit falls inside the window. Using the baseline (not a hardcoded version) makes each notebook run internally consistent and re-runnable (mitigation for the non-idempotent update).

**Alternatives considered**:
- *Timestamp-based `table_changes(table, startingTimestamp)`*: Works, but version numbers are exact and avoid timezone/precision ambiguity. Rejected in favor of version.
- *Reading from version 0*: Would include unrelated historical commits and (for changes before CDF was enabled) is not supported. Rejected.

**Important nuance**: CDF only records change data for commits made **after** `enableChangeDataFeed=true`. Therefore the order is mandatory: enable CDF → capture baseline → UPDATE. The plan and contract enforce this ordering.

---

## Decision 3: The safe test update

**Decision**: `UPDATE databricks_arrow_cata.bronz.sales_info SET sls_price = sls_price * 1.15 WHERE sls_ord_num = 'SO43697';` Capture old price by reading the row before the update; capture new price by reading after. Report `num_affected_rows` and warn if zero.

**Rationale**: Matches PLAN.md's recommended test update exactly. Scoping to a single `sls_ord_num` keeps the blast radius to one order. Reading the row before/after gives human-visible old/new values independent of the CDF read (a second, corroborating source of truth).

**Alternatives considered**:
- *Insert a temporary row then update it*: Avoids mutating real data but does not match PLAN.md and would not validate CDF on the actual monitored data. Rejected.
- *MERGE instead of UPDATE*: Unnecessary complexity for a single-key change. Rejected.

---

## Decision 4: Validating pre-image / post-image

**Decision**: Query `table_changes(table, baseline)` filtered to `sls_ord_num = 'SO43697'`, then assert presence of at least one row with `_change_type = 'update_preimage'` and at least one with `_change_type = 'update_postimage'`. Extract old `sls_price` from the pre-image row and new `sls_price` from the post-image row. Print `SUCCESS` only if both exist; otherwise `FAILED` with the reason.

**Rationale**: Delta CDF represents an UPDATE as a matched pair (`update_preimage`, `update_postimage`) sharing the same `_commit_version`. Checking both proves CDF captured the full before/after state — the explicit Phase 001 acceptance criterion.

**Alternatives considered**:
- *Only check `update_postimage`*: Insufficient — the spec requires proving the **old** value is captured too. Rejected.
- *Count-based assertion across all change types*: Less precise; explicit `_change_type` checks give clearer PASS/FAIL diagnostics. Rejected.

---

## Decision 5: Rollback handling

**Decision**: Print a ready-to-paste rollback statement (`UPDATE ... SET sls_price = sls_price / 1.15 WHERE sls_ord_num = 'SO43697';`) and explicitly **do not** execute it. The notebook leaves the +15% change in place.

**Rationale**: The spec/scope says "print rollback SQL suggestion but do not auto-rollback." Leaving rollback manual avoids destroying the very change records the validation just produced and keeps the operator in control of the bronze table.

**Alternatives considered**:
- *Auto-rollback after validation*: Would revert the test change automatically, but it (a) violates the explicit instruction and (b) adds another non-idempotent write. Rejected.

---

## Decision 6: Configuration source

**Decision**: Add Phase 001 constants to `src/cdf_agent_monitoring/config.py` (`TEST_ORDER_NUM = "SO43697"`, `PRICE_MULTIPLIER = 1.15`) and have the notebook load `config` via the same `sys.path` insertion pattern used by `notebooks/00_project_bootstrap.py`. `SOURCE_TABLE`, `BUSINESS_KEY_COLUMNS`, and `WATCHED_COLUMN` are reused from existing config.

**Rationale**: Centralizes constants, avoids magic strings, and matches the established Phase 000 convention. Keeps the notebook consistent and reduces drift across phases.

**Alternatives considered**:
- *Hardcode constants in the notebook*: Faster but diverges from the project pattern and duplicates `SOURCE_TABLE`. Rejected.
- *Databricks widgets for parameters*: Over-engineered for a fixed single-order validation. Rejected for this phase.

---

## Resolved unknowns

| Item | Resolution |
|------|------------|
| Starting version semantics for `table_changes()` | Inclusive of `startingVersion`; capture baseline before UPDATE. |
| CDF availability for pre-enablement commits | Not available; enablement must precede the captured baseline and the UPDATE. |
| Where constants live | `src/cdf_agent_monitoring/config.py`, loaded via `sys.path`. |
| File locations | `sql/007_enable_cdf.sql`, `notebooks/01_enable_cdf_and_validate.py` (rewrite the existing stub). |

No `NEEDS CLARIFICATION` markers remain.
