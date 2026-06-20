# Databricks notebook source
# Phase 000 - Project Bootstrap

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
EXPECTED_MONITORING_TABLES = {
    "agent_rules",
    "change_events",
    "agent_alerts",
    "notification_log",
    "agent_run_log",
}


def run_sql(label, sql_text):
    print(f"[RUN] {label}")
    result = spark.sql(sql_text)
    print(f"[OK] {label}")
    return result


print("Phase 000 Databricks CDF agent monitoring bootstrap")
print("Serverless compute only. This notebook does not enable CDF or modify source data.")
print(f"SOURCE_TABLE = {SOURCE_TABLE}")
print(f"MONITORING_SCHEMA = {MONITORING_SCHEMA}")
print(f"RULE_ID = {RULE_ID}")
print(f"BUSINESS_KEY_COLUMNS = {BUSINESS_KEY_COLUMNS}")
print(f"CONTEXT_COLUMNS = {CONTEXT_COLUMNS}")
print(f"WATCHED_COLUMN = {WATCHED_COLUMN}")
print(f"MEDIUM_THRESHOLD_PERCENT = {MEDIUM_THRESHOLD_PERCENT}")
print(f"HIGH_THRESHOLD_PERCENT = {HIGH_THRESHOLD_PERCENT}")

# COMMAND ----------

try:
    run_sql("Validate source table access", f"DESCRIBE TABLE {SOURCE_TABLE}").collect()
except Exception as exc:
    raise RuntimeError(
        f"Source table {SOURCE_TABLE} is not accessible. Confirm the table exists and your user has read permissions."
    ) from exc

# COMMAND ----------

print("Creating monitoring schema and tables")

run_sql("Create monitoring schema", f"CREATE SCHEMA IF NOT EXISTS {MONITORING_SCHEMA}")

run_sql(
    "Create agent_rules table",
    f"""
    CREATE TABLE IF NOT EXISTS {RULES_TABLE} (
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
    USING DELTA
    """,
)

run_sql(
    "Create change_events table",
    f"""
    CREATE TABLE IF NOT EXISTS {EVENTS_TABLE} (
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
    USING DELTA
    """,
)

run_sql(
    "Create agent_alerts table",
    f"""
    CREATE TABLE IF NOT EXISTS {ALERTS_TABLE} (
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
    USING DELTA
    """,
)

run_sql(
    "Create notification_log table",
    f"""
    CREATE TABLE IF NOT EXISTS {NOTIFICATION_LOG_TABLE} (
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
    USING DELTA
    """,
)

run_sql(
    "Create agent_run_log table",
    f"""
    CREATE TABLE IF NOT EXISTS {RUN_LOG_TABLE} (
      run_id STRING NOT NULL,
      phase STRING NOT NULL,
      status STRING NOT NULL,
      message STRING,
      row_count BIGINT,
      created_at TIMESTAMP NOT NULL,
      completed_at TIMESTAMP,
      CONSTRAINT agent_run_log_pk PRIMARY KEY (run_id) NOT ENFORCED
    )
    USING DELTA
    """,
)

tables_df = run_sql("Show monitoring tables", f"SHOW TABLES IN {MONITORING_SCHEMA}")
display(tables_df)
actual_tables = {row.tableName for row in tables_df.collect()}
missing_tables = EXPECTED_MONITORING_TABLES - actual_tables
if missing_tables:
    raise RuntimeError(f"Missing monitoring tables after bootstrap: {sorted(missing_tables)}")
print(f"[OK] Monitoring tables validated: {sorted(EXPECTED_MONITORING_TABLES)}")

# COMMAND ----------

print("Source table discovery")

display(run_sql("Describe source table", f"DESCRIBE TABLE {SOURCE_TABLE}"))
display(run_sql("Describe source detail", f"DESCRIBE DETAIL {SOURCE_TABLE}"))

properties_df = run_sql("Show source table properties", f"SHOW TBLPROPERTIES {SOURCE_TABLE}")
display(properties_df)

cdf_rows = [row for row in properties_df.collect() if row.key == "delta.enableChangeDataFeed"]
cdf_status = cdf_rows[0].value if cdf_rows else "not set"
print(f"CDF status for {SOURCE_TABLE}: {cdf_status}")
print("Phase 000 documents CDF status only. It does not enable or disable CDF.")

display(run_sql("Describe source history", f"DESCRIBE HISTORY {SOURCE_TABLE}"))
display(run_sql("Sample source rows", f"SELECT * FROM {SOURCE_TABLE} LIMIT 20"))

# COMMAND ----------

print("Phase 000 bootstrap complete")
print("No source table update was run.")
print("No CDF enablement was run.")
print("No table_changes() call was run.")
print("No rule-based agent, notification, Genie, LangChain, OpenAI, RAG, or external webhook logic was run.")
