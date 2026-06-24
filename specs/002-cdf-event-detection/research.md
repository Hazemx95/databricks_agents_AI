# Phase 0 Research: CDF Event Detection (Phase 002)

All open questions from the spec's Assumptions and the user-supplied plan are resolved below.

## R1. Event-row fields vs. the actual `change_events` schema

**Question**: The plan input lists event fields `business_key`, `change_type`, `event_status`, `source_table_full_name` that do not appear in the `change_events` table.

**Live schema confirmed** (`DESCRIBE databricks_arrow_cata.monitoring.change_events`), 13 columns:
`event_id, rule_id, event_type, source_table, business_key_json, old_value, new_value, change_percent, context_json, watched_column, commit_version, commit_timestamp, created_at`.

**Decision**: Persist exactly these 13 columns. Treat the extra requested names as **internal helper columns** on the working DataFrame only:
- `business_key` (plain string of `sls_ord_num`) — used to build `business_key_json` and as a readable MERGE join helper; not persisted.
- `change_type` — derived from CDF metadata for clarity during display; not persisted (no column for it).
- `event_status` — dropped (no column; adding one is out of scope).
- `source_table_full_name` — maps to the existing `source_table` column (holds the FQN).

**Rationale**: FR-010 requires event rows to match the schema exactly; out-of-scope forbids altering tables. Helper columns aid readability/joins without breaking the contract.

**Alternatives rejected**: Altering `change_events` to add `event_status`/`change_type` — explicitly out of scope and would diverge from the constitution's table definition.

## R2. Deduplication key mapping

**Question**: Constitution/spec dedup key is (`rule_id`, business key, `watched_column`, `commit_version`); the table has no plain `business_key` column.

**Decision**: MERGE `ON target.rule_id = source.rule_id AND target.business_key_json = source.business_key_json AND target.watched_column = source.watched_column AND target.commit_version = source.commit_version`, with `WHEN NOT MATCHED THEN INSERT`. No `WHEN MATCHED` clause (insert-only; existing events untouched).

**Rationale**: `business_key_json` is a deterministic function of `sls_ord_num` (`{"sls_ord_num": "<v>"}`), so matching on it is equivalent to matching on the business key. Insert-only guarantees idempotency (SC-004) and leaves prior rows immutable (constitution IV/V).

**Alternatives rejected**: Dedup via `event_id` — `event_id` is freshly generated per run (e.g., UUID), so it cannot detect a re-detected change. Dedup via `NOT EXISTS` INSERT — equivalent but MERGE is the idiomatic, atomic Delta pattern.

## R3. `change_percent` computation and edge handling

**Decision**: `calculate_change_percent(old, new)` returns the signed percentage `((new-old)/old)*100`, rounded to a consistent precision (2 decimals). Returns `None` when:
- `old` or `new` is `None`/null,
- `old` or `new` is non-numeric (cannot be coerced to float),
- `old` is zero.

Test vectors (from plan input): `100→115 ⇒ 15`, `100→80 ⇒ -20`, `100→100 ⇒ 0`, `0→100 ⇒ None`, any-`None` ⇒ `None`, non-numeric ⇒ `None`.

**Rationale**: Avoids divide-by-zero (FR-007); `None`→SQL `NULL` in the DOUBLE column. The event is still emitted when percent is `None` (the change is real; only the percentage is undefined) — consistent with spec Assumptions.

**Alternatives rejected**: Raising on bad input — would crash the notebook on dirty data; returning `0` for zero-old — misleading (it is an undefined percentage, not a 0% change).

## R4. CDF read window (start/end version)

**Decision**: Notebook exposes `start_version` and `end_version` widgets (strings). Print the selected versions. Read `spark.read.format("delta").option("readChangeFeed","true").option("startingVersion", start).option("endingVersion", end)` (or SQL `table_changes(SOURCE_TABLE, start, end)`). If `end_version` is blank/empty, omit the ending bound so the read runs from `start_version` to the latest available version.

**Rationale**: Matches plan input; idempotent MERGE makes overlapping windows safe (re-reading already-persisted changes inserts nothing). Default `start_version = 0` reads the full available feed on a fresh run.

**Alternatives rejected**: Hardcoding versions — not reproducible/operable; tracking a persisted high-watermark — premature for this phase and unnecessary given idempotency.

## R5. Pairing pre-image and post-image rows

**Decision**: From `table_changes()`, filter `_change_type = 'update_preimage'` (old) and `_change_type = 'update_postimage'` (new). Inner-join old↔new on `sls_ord_num` **and** `_commit_version`. Each pair yields one old/new `sls_price` plus post-image context columns.

**Rationale**: A given order is updated at most once per commit (spec Assumption), so (`sls_ord_num`, `_commit_version`) uniquely identifies a pair. Inner join naturally drops unmatched/orphan images (edge case "unpaired image rows"). Insert/delete/`update` change types are excluded by the filter (FR-003).

## R6. Spark-free helper boundary

**Decision**: `event_builder.py` imports only the standard library (`json`). It operates on plain Python values / dict-like rows, not Spark `Row`/`Column` objects. The notebook converts the paired DataFrame to the values it passes into the helpers (or applies them via a UDF/`mapInPandas`/driver-side collect for the small result set).

**Rationale**: Enables fast local `pytest` (no cluster) and satisfies the explicit "No Spark dependency in this module" rule. Keeps pure logic unit-tested and Spark orchestration in the notebook.

## R7. Live validation requirement (FR-018)

**Confirmed live**: `SHOW TBLPROPERTIES` on the source table returns `delta.enableChangeDataFeed = true`; `change_events` exists with the 13 columns above. Phase 002 success must be demonstrated by running the notebook against the workspace (via Databricks MCP / DEFAULT `.databrickscfg`) and showing the resulting `change_events` rows — not from local code generation alone.
