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
