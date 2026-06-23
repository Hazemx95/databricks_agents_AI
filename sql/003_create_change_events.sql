CREATE TABLE IF NOT EXISTS databricks_arrow_cata.monitoring.change_events (
  event_id STRING NOT NULL,
  rule_id STRING NOT NULL,
  event_type STRING NOT NULL,
  source_table STRING NOT NULL,
  business_key_json STRING NOT NULL,
  old_value STRING,
  new_value STRING,
  change_percent DOUBLE,
  context_json STRING,
  watched_column STRING NOT NULL,
  commit_version BIGINT NOT NULL,
  commit_timestamp TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL,
  CONSTRAINT change_events_pk PRIMARY KEY (event_id) NOT ENFORCED
)
USING DELTA;
