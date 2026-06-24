# Contract: `agent_rules` MERGE Upsert

**Target**: `databricks_arrow_cata.monitoring.agent_rules`
**Operation**: idempotent upsert of one rule, matched on `rule_id`.

## Preconditions

- Table exists (created by `sql/002_create_agent_rules.sql`, `CREATE TABLE IF NOT EXISTS`).
- All 16 columns present as in [data-model.md](../data-model.md).

## Source

A single-row relation with the 14 business columns (all columns except `created_at`, `updated_at`). Provided as a temp view built from `config.py` constants, or inline `VALUES`.

## MERGE semantics

```sql
MERGE INTO databricks_arrow_cata.monitoring.agent_rules AS target
USING (<one-row source>) AS source
ON target.rule_id = source.rule_id
WHEN MATCHED THEN UPDATE SET
  rule_name                 = source.rule_name,
  catalog_name              = source.catalog_name,
  schema_name               = source.schema_name,
  table_name                = source.table_name,
  business_key_columns      = source.business_key_columns,
  context_columns           = source.context_columns,
  watched_column            = source.watched_column,
  condition_type            = source.condition_type,
  medium_threshold_percent  = source.medium_threshold_percent,
  high_threshold_percent    = source.high_threshold_percent,
  notification_target_type  = source.notification_target_type,
  notification_target_value = source.notification_target_value,
  is_active                 = source.is_active,
  updated_at                = current_timestamp()
WHEN NOT MATCHED THEN INSERT (
  rule_id, rule_name, catalog_name, schema_name, table_name,
  business_key_columns, context_columns, watched_column, condition_type,
  medium_threshold_percent, high_threshold_percent,
  notification_target_type, notification_target_value, is_active,
  created_at, updated_at
) VALUES (
  source.rule_id, source.rule_name, source.catalog_name, source.schema_name, source.table_name,
  source.business_key_columns, source.context_columns, source.watched_column, source.condition_type,
  source.medium_threshold_percent, source.high_threshold_percent,
  source.notification_target_type, source.notification_target_value, source.is_active,
  current_timestamp(), current_timestamp()
);
```

## Postconditions / Guarantees

- Exactly one row exists where `rule_id = 'SALES_PRICE_CHANGE_001'`.
- That row's values equal the canonical values in [data-model.md](../data-model.md).
- `created_at` is set once (insert); `updated_at` reflects the latest write.
- Re-running the MERGE does not change the row count (idempotent, SC-003).
- `WHEN MATCHED` does **not** overwrite `created_at`.

## Values (canonical)

| Column | Value |
|--------|-------|
| rule_id | `SALES_PRICE_CHANGE_001` |
| rule_name | `Sales price change monitoring` |
| catalog_name | `databricks_arrow_cata` |
| schema_name | `bronz` |
| table_name | `sales_info` |
| business_key_columns | `sls_ord_num` |
| context_columns | `sls_prd_key,sls_cust_id,sls_quantity,sls_sales` |
| watched_column | `sls_price` |
| condition_type | `percent_change` |
| medium_threshold_percent | `5.0` |
| high_threshold_percent | `10.0` |
| notification_target_type | `alert_table` |
| notification_target_value | `databricks_arrow_cata.monitoring.notification_log` |
| is_active | `true` |
