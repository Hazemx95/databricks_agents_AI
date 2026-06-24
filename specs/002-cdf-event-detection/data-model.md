# Phase 1 Data Model: CDF Event Detection (Phase 002)

## Entities

### 1. CDF Change Row (read-only, transient)

Returned by `table_changes('databricks_arrow_cata.bronz.sales_info', start, end)`.

| Field | Type | Notes |
|-------|------|-------|
| sls_ord_num | string | Business key |
| sls_price | (numeric/string) | Watched column |
| sls_prd_key, sls_cust_id, sls_quantity, sls_sales | various | Context columns |
| _change_type | string | One of `insert`, `update_preimage`, `update_postimage`, `delete` |
| _commit_version | bigint | Delta commit version of the change |
| _commit_timestamp | timestamp | Commit time |

Only `update_preimage` and `update_postimage` rows are retained (FR-003).

### 2. Paired Change (transient working DataFrame)

One row per (`sls_ord_num`, `_commit_version`) update, joining old↔new.

| Field | Source | Notes |
|-------|--------|-------|
| sls_ord_num | both images | Join key |
| commit_version | both images (`_commit_version`) | Join key |
| commit_timestamp | post-image (`_commit_timestamp`) | Provenance |
| old_value | pre-image `sls_price` | string-cast for storage |
| new_value | post-image `sls_price` | string-cast for storage |
| sls_prd_key, sls_cust_id, sls_quantity, sls_sales | post-image | For `context_json` |
| change_type *(helper)* | derived | Not persisted |
| business_key *(helper)* | `sls_ord_num` | Not persisted |

Retained only when `old_value != new_value` (FR-005).

### 3. Change Event (persisted → `databricks_arrow_cata.monitoring.change_events`)

**Exact persisted schema (13 columns) — no additions, no omissions:**

| Column | Type | Source / Value | Null? |
|--------|------|----------------|-------|
| event_id | string | Generated unique id (e.g., UUID) per detected change | NOT NULL |
| rule_id | string | `SALES_PRICE_CHANGE_001` (config.RULE_ID) | NOT NULL |
| event_type | string | `SALES_PRICE_CHANGE` | NOT NULL |
| source_table | string | `databricks_arrow_cata.bronz.sales_info` (FQN) | NOT NULL |
| business_key_json | string | `build_business_key(row, ["sls_ord_num"])` → `{"sls_ord_num":"<v>"}` | NOT NULL |
| old_value | string | pre-image `sls_price` as string | nullable |
| new_value | string | post-image `sls_price` as string | nullable |
| change_percent | double | `calculate_change_percent(old, new)`; `None`→NULL | nullable |
| context_json | string | `build_json_from_columns(row, CONTEXT_COLUMNS)` | nullable |
| watched_column | string | `sls_price` (config.WATCHED_COLUMN) | NOT NULL |
| commit_version | bigint | pair `_commit_version` | NOT NULL |
| commit_timestamp | timestamp | pair `_commit_timestamp` | NOT NULL |
| created_at | timestamp | `current_timestamp()` at write | NOT NULL |

**Deduplication key**: (`rule_id`, `business_key_json`, `watched_column`, `commit_version`) — equivalent to (`rule_id`, business key `sls_ord_num`, `watched_column`, `commit_version`).

## Validation Rules

- `business_key_json` and `context_json` MUST be valid JSON strings.
- No NOT NULL column may be null in a persisted row (SC-003).
- A pair with identical old/new `sls_price` MUST NOT produce an event (SC-005).
- Re-detecting an already-persisted change MUST insert zero rows (SC-004).
- `change_percent` is `NULL` only when old/new is null, non-numeric, or old is zero; otherwise it equals the signed % within 2-decimal precision (SC-002).

## Helper Module Contract (`event_builder.py`, Spark-free)

| Function | Signature | Returns |
|----------|-----------|---------|
| `calculate_change_percent` | `(old_value, new_value)` | `float` signed % rounded to 2 dp, or `None` (null / non-numeric / old==0) |
| `build_business_key` | `(row, key_columns)` | JSON string of `{col: row[col]}` for each key column |
| `build_json_from_columns` | `(row, columns)` | JSON string of `{col: row[col]}` for each listed column |

`row` is any mapping/dict-like (supports `row[col]`); no Spark types.
