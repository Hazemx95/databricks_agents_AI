from pathlib import Path
import sys

PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "src").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cdf_agent_monitoring import config 

SOURCE_TABLE = config.SOURCE_TABLE
MONITORING_SCHEMA = config.MONITORING_SCHEMA
RULE_ID = config.RULE_ID
BUSINESS_KEY_COLUMNS = config.BUSINESS_KEY_COLUMNS
CONTEXT_COLUMNS = config.CONTEXT_COLUMNS
WATCHED_COLUMN = config.WATCHED_COLUMN
MEDIUM_THRESHOLD_PERCENT = config.MEDIUM_THRESHOLD_PERCENT
HIGH_THRESHOLD_PERCENT = config.HIGH_THRESHOLD_PERCENT

SQL_DIR = PROJECT_ROOT / "sql"
PHASE_000_SQL_FILES = [
    "001_create_monitoring_schema.sql",
    "002_create_agent_rules.sql",
    "003_create_change_events.sql",
    "004_create_agent_alerts.sql",
    "005_create_notification_log.sql",
    "006_create_agent_run_log.sql",
]
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

for sql_file in PHASE_000_SQL_FILES:
    run_sql(sql_file, (SQL_DIR / sql_file).read_text())

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
