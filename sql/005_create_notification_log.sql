CREATE TABLE IF NOT EXISTS databricks_arrow_cata.monitoring.notification_log (
  notification_id STRING NOT NULL,
  alert_id STRING NOT NULL,
  rule_id STRING NOT NULL,
  notification_type STRING NOT NULL,
  subject STRING,
  body STRING NOT NULL,
  delivery_status STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  sent_at TIMESTAMP,
  CONSTRAINT notification_log_pk PRIMARY KEY (notification_id) NOT ENFORCED
)
USING DELTA;
