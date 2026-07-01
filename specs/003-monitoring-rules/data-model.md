# Phase 003 Data Model: Monitoring Rules Table (Phase 003)

## Entities

### 1. Monitoring Rule (persisted → `databricks_arrow_cata.monitoring.agent_rules`)

The single entity of this phase. Schema verified live against `information_schema` — **16 columns, no additions, no omissions.** Primary key `rule_id` (NOT ENFORCED).

| Column | Type | Phase 003 value for `SALES_PRICE_CHANGE_001` | Null? | Source |
|--------|------|-----------------------------------------------|-------|--------|
| rule_id | STRING | `SALES_PRICE_CHANGE_001` | NOT NULL | `config.RULE_ID` |
| rule_name | STRING | `Sales price change monitoring` | NOT NULL | `config.RULE_NAME` (new) |
| catalog_name | STRING | `databricks_arrow_cata` | NOT NULL | `config.SOURCE_CATALOG` (new) |
| schema_name | STRING | `bronz` (source schema) | NOT NULL | `config.SOURCE_SCHEMA` (new) |
| table_name | STRING | `sales_info` | NOT NULL | `config.SOURCE_TABLE_NAME` (new) |
| business_key_columns | STRING | `sls_ord_num` | NOT NULL | `",".join(config.BUSINESS_KEY_COLUMNS)` |
| context_columns | STRING | `sls_prd_key,sls_cust_id,sls_quantity,sls_sales` | NOT NULL | `",".join(config.CONTEXT_COLUMNS)` |
| watched_column | STRING | `sls_price` | NOT NULL | `config.WATCHED_COLUMN` |
| condition_type | STRING | `percent_change` | NOT NULL | `config.CONDITION_TYPE` (new) |
| medium_threshold_percent | DOUBLE | `5.0` | NOT NULL | `config.MEDIUM_THRESHOLD_PERCENT` |
| high_threshold_percent | DOUBLE | `10.0` | NOT NULL | `config.HIGH_THRESHOLD_PERCENT` |
| notification_target_type | STRING | `alert_table` | NOT NULL | `config.NOTIFICATION_TARGET_TYPE` (new) |
| notification_target_value | STRING | `databricks_arrow_cata.monitoring.notification_log` | NOT NULL | `config.NOTIFICATION_TARGET_VALUE` (new) = `config.NOTIFICATION_LOG_TABLE` |
| is_active | BOOLEAN | `true` | NOT NULL | literal `True` |
| created_at | TIMESTAMP | `current_timestamp()` (insert only) | NOT NULL | set in MERGE |
| updated_at | TIMESTAMP | `current_timestamp()` (insert + update) | NOT NULL | set in MERGE |

**Match / dedup key**: `rule_id` (the primary key). The primary key is not enforced by Delta, so the notebook fails fast if pre-existing duplicate `rule_id` rows exist before running the `MERGE`.

### 2. Rule Source Row (transient working set for the MERGE)

A one-row source (temp view or `VALUES`) carrying the 14 business columns above (all except `created_at`/`updated_at`, which the MERGE sets via `current_timestamp()`). Not persisted as a separate object.

## Config Constants (src/cdf_agent_monitoring/config.py)

**Reused (already present):** `RULE_ID`, `BUSINESS_KEY_COLUMNS`, `CONTEXT_COLUMNS`, `WATCHED_COLUMN`, `MEDIUM_THRESHOLD_PERCENT`, `HIGH_THRESHOLD_PERCENT`, `RULES_TABLE`, `NOTIFICATION_LOG_TABLE`, `SOURCE_TABLE`, `MONITORING_SCHEMA`.

**To add:**

| Constant | Value |
|----------|-------|
| `RULE_NAME` | `"Sales price change monitoring"` |
| `EVENT_TYPE` | `"SALES_PRICE_CHANGE"` (reserved for Phase 004; not written to the Phase 003 `agent_rules` schema) |
| `CONDITION_TYPE` | `"percent_change"` |
| `NOTIFICATION_TARGET_TYPE` | `"alert_table"` |
| `NOTIFICATION_TARGET_VALUE` | `NOTIFICATION_LOG_TABLE` (= `databricks_arrow_cata.monitoring.notification_log`) |
| `SOURCE_CATALOG` | `"databricks_arrow_cata"` |
| `SOURCE_SCHEMA` | `"bronz"` |
| `SOURCE_TABLE_NAME` | `"sales_info"` |

These keep `SOURCE_TABLE == f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.{SOURCE_TABLE_NAME}"` consistent. `EVENT_TYPE` is a forward-looking rule-based agent constant only; the current Phase 003 schema does not include an `event_type` column.

## Validation Rules (enforced by the notebook)

| ID | Check | Expected | Maps to |
|----|-------|----------|---------|
| V1 | `agent_rules` table exists | present | FR-001, US1 |
| V2 | active rows for `SALES_PRICE_CHANGE_001` | count == 1 | FR-006, SC-001 |
| V3 | `is_active` | `true` | US3-AS1 |
| V4 | `watched_column` | `sls_price` | US3-AS3, SC-002 |
| V5 | `business_key_columns` | `sls_ord_num` | US3-AS3, SC-002 |
| V6 | `context_columns` | `sls_prd_key,sls_cust_id,sls_quantity,sls_sales` | US3-AS3 |
| V7 | `medium_threshold_percent` | `5.0` | US3-AS4, SC-002 |
| V8 | `high_threshold_percent` | `10.0` | US3-AS4, SC-002 |
| V9 | `catalog_name`/`schema_name`/`table_name` resolve to `databricks_arrow_cata.bronz.sales_info` | match | US3-AS2, SC-002 |
| V10 | `condition_type` | `percent_change` | US3-AS4 |
| V11 | `notification_target_type` / `notification_target_value` | `alert_table` / `databricks_arrow_cata.monitoring.notification_log` | US3-AS5 |

All pass → notebook prints `SUCCESS`; any fail → `FAILED: <reasons>`.

## State / Idempotency

- **First run**: `WHEN NOT MATCHED` → INSERT one row; `created_at = updated_at = current_timestamp()`.
- **Subsequent runs**: `WHEN MATCHED` → UPDATE business columns + `updated_at`; `created_at` unchanged; row count for the rule stays at exactly 1 (SC-003).
- Source table `bronz.sales_info` is never read or modified by this phase.
