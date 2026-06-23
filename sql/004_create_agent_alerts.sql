CREATE TABLE IF NOT EXISTS databricks_arrow_cata.monitoring.agent_alerts (
  alert_id STRING NOT NULL,
  event_id STRING NOT NULL,
  rule_id STRING NOT NULL,
  severity STRING NOT NULL,
  should_notify BOOLEAN NOT NULL,
  reason STRING NOT NULL,
  recommended_action STRING,
  agent_type STRING NOT NULL,
  alert_status STRING NOT NULL,
  genie_context_json STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  CONSTRAINT agent_alerts_pk PRIMARY KEY (alert_id) NOT ENFORCED
)
USING DELTA;
