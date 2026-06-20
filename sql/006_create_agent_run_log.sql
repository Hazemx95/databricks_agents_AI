CREATE TABLE IF NOT EXISTS databricks_arrow_cata.monitoring.agent_run_log (
  run_id STRING NOT NULL,
  phase STRING NOT NULL,
  status STRING NOT NULL,
  message STRING,
  row_count BIGINT,
  created_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  CONSTRAINT agent_run_log_pk PRIMARY KEY (run_id) NOT ENFORCED
)
USING DELTA;
