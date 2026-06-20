"""Project constants for Phase 000 bootstrap."""

SOURCE_TABLE = "databricks_arrow_cata.bronz.sales_info"
MONITORING_SCHEMA = "databricks_arrow_cata.monitoring"

RULE_ID = "SALES_PRICE_CHANGE_001"
BUSINESS_KEY_COLUMNS = ["sls_ord_num"]
CONTEXT_COLUMNS = ["sls_prd_key", "sls_cust_id", "sls_quantity", "sls_sales"]
WATCHED_COLUMN = "sls_price"

MEDIUM_THRESHOLD_PERCENT = 5.0
HIGH_THRESHOLD_PERCENT = 10.0

RULES_TABLE = f"{MONITORING_SCHEMA}.agent_rules"
EVENTS_TABLE = f"{MONITORING_SCHEMA}.change_events"
ALERTS_TABLE = f"{MONITORING_SCHEMA}.agent_alerts"
NOTIFICATION_LOG_TABLE = f"{MONITORING_SCHEMA}.notification_log"
RUN_LOG_TABLE = f"{MONITORING_SCHEMA}.agent_run_log"
