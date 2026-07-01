-- Phase 003 reference script: idempotently creates agent_rules and upserts the first rule.
CREATE TABLE IF NOT EXISTS databricks_arrow_cata.monitoring.agent_rules (
  rule_id STRING NOT NULL,
  rule_name STRING NOT NULL,
  catalog_name STRING NOT NULL,
  schema_name STRING NOT NULL,
  table_name STRING NOT NULL,
  business_key_columns STRING NOT NULL,
  context_columns STRING NOT NULL,
  watched_column STRING NOT NULL,
  condition_type STRING NOT NULL,
  medium_threshold_percent DOUBLE NOT NULL,
  high_threshold_percent DOUBLE NOT NULL,
  notification_target_type STRING NOT NULL,
  notification_target_value STRING NOT NULL,
  is_active BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  CONSTRAINT agent_rules_pk PRIMARY KEY (rule_id) NOT ENFORCED
)
USING DELTA;

MERGE INTO databricks_arrow_cata.monitoring.agent_rules AS target
USING (
  SELECT
    'SALES_PRICE_CHANGE_001' AS rule_id,
    'Sales price change monitoring' AS rule_name,
    'databricks_arrow_cata' AS catalog_name,
    'bronz' AS schema_name,
    'sales_info' AS table_name,
    'sls_ord_num' AS business_key_columns,
    'sls_prd_key,sls_cust_id,sls_quantity,sls_sales' AS context_columns,
    'sls_price' AS watched_column,
    'percent_change' AS condition_type,
    CAST(5.0 AS DOUBLE) AS medium_threshold_percent,
    CAST(10.0 AS DOUBLE) AS high_threshold_percent,
    'alert_table' AS notification_target_type,
    'databricks_arrow_cata.monitoring.notification_log' AS notification_target_value,
    true AS is_active
) AS source
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
  rule_id,
  rule_name,
  catalog_name,
  schema_name,
  table_name,
  business_key_columns,
  context_columns,
  watched_column,
  condition_type,
  medium_threshold_percent,
  high_threshold_percent,
  notification_target_type,
  notification_target_value,
  is_active,
  created_at,
  updated_at
) VALUES (
  source.rule_id,
  source.rule_name,
  source.catalog_name,
  source.schema_name,
  source.table_name,
  source.business_key_columns,
  source.context_columns,
  source.watched_column,
  source.condition_type,
  source.medium_threshold_percent,
  source.high_threshold_percent,
  source.notification_target_type,
  source.notification_target_value,
  source.is_active,
  current_timestamp(),
  current_timestamp()
);
