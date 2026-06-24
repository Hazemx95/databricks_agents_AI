"""Project constants for the Databricks CDF monitoring workflow."""

SOURCE_CATALOG = "databricks_arrow_cata"
SOURCE_SCHEMA = "bronz"
SOURCE_TABLE_NAME = "sales_info"
SOURCE_TABLE = f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.{SOURCE_TABLE_NAME}"
MONITORING_SCHEMA = "databricks_arrow_cata.monitoring"

RULE_ID = "SALES_PRICE_CHANGE_001"
RULE_NAME = "Sales price change monitoring"
EVENT_TYPE = "SALES_PRICE_CHANGE"
BUSINESS_KEY_COLUMNS = ["sls_ord_num"]
CONTEXT_COLUMNS = ["sls_prd_key", "sls_cust_id", "sls_quantity", "sls_sales"]
WATCHED_COLUMN = "sls_price"
CONDITION_TYPE = "percent_change"

MEDIUM_THRESHOLD_PERCENT = 5.0
HIGH_THRESHOLD_PERCENT = 10.0

RULES_TABLE = f"{MONITORING_SCHEMA}.agent_rules"
EVENTS_TABLE = f"{MONITORING_SCHEMA}.change_events"
ALERTS_TABLE = f"{MONITORING_SCHEMA}.agent_alerts"
NOTIFICATION_LOG_TABLE = f"{MONITORING_SCHEMA}.notification_log"
NOTIFICATION_TARGET_TYPE = "alert_table"
NOTIFICATION_TARGET_VALUE = NOTIFICATION_LOG_TABLE
RUN_LOG_TABLE = f"{MONITORING_SCHEMA}.agent_run_log"
