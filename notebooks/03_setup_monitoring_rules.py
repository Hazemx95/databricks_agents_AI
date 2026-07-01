# Databricks notebook source
# Phase 003 - Setup Monitoring Rules

from pathlib import Path
import sys


def _add_project_src_to_path():
    candidates = []

    cwd = Path.cwd()
    candidates.extend([cwd / "src", cwd.parent / "src"])

    if "dbutils" in globals():
        notebook_path = (
            dbutils.notebook.entry_point.getDbutils()
            .notebook()
            .getContext()
            .notebookPath()
            .get()
        )
        workspace_root = Path("/Workspace") / notebook_path.lstrip("/")
        candidates.extend([workspace_root.parent.parent / "src", workspace_root.parent / "src"])

    for candidate in candidates:
        if candidate.exists() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))


_add_project_src_to_path()

try:
    from cdf_agent_monitoring import config
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Could not import cdf_agent_monitoring.config. Sync or upload the repository with its src/ "
        "directory before running notebooks/03_setup_monitoring_rules.py."
    ) from exc

RULES_TABLE = config.RULES_TABLE
RULE_ID = config.RULE_ID
RULE_NAME = config.RULE_NAME
SOURCE_CATALOG = config.SOURCE_CATALOG
SOURCE_SCHEMA = config.SOURCE_SCHEMA
SOURCE_TABLE_NAME = config.SOURCE_TABLE_NAME
SOURCE_TABLE = config.SOURCE_TABLE
BUSINESS_KEY_COLUMNS = ",".join(config.BUSINESS_KEY_COLUMNS)
CONTEXT_COLUMNS = ",".join(config.CONTEXT_COLUMNS)
WATCHED_COLUMN = config.WATCHED_COLUMN
CONDITION_TYPE = config.CONDITION_TYPE
MEDIUM_THRESHOLD_PERCENT = config.MEDIUM_THRESHOLD_PERCENT
HIGH_THRESHOLD_PERCENT = config.HIGH_THRESHOLD_PERCENT
NOTIFICATION_TARGET_TYPE = config.NOTIFICATION_TARGET_TYPE
NOTIFICATION_TARGET_VALUE = config.NOTIFICATION_TARGET_VALUE
IS_ACTIVE = True


def sql_string(value):
    return str(value).replace("'", "''")


def run_sql(label, sql_text):
    print(f"[RUN] {label}")
    result = spark.sql(sql_text)
    print(f"[OK] {label}")
    return result


def scalar(sql_text):
    return spark.sql(sql_text).collect()[0][0]


def rule_literal_select():
    return f"""
      SELECT
        '{sql_string(RULE_ID)}' AS rule_id,
        '{sql_string(RULE_NAME)}' AS rule_name,
        '{sql_string(SOURCE_CATALOG)}' AS catalog_name,
        '{sql_string(SOURCE_SCHEMA)}' AS schema_name,
        '{sql_string(SOURCE_TABLE_NAME)}' AS table_name,
        '{sql_string(BUSINESS_KEY_COLUMNS)}' AS business_key_columns,
        '{sql_string(CONTEXT_COLUMNS)}' AS context_columns,
        '{sql_string(WATCHED_COLUMN)}' AS watched_column,
        '{sql_string(CONDITION_TYPE)}' AS condition_type,
        CAST({MEDIUM_THRESHOLD_PERCENT} AS DOUBLE) AS medium_threshold_percent,
        CAST({HIGH_THRESHOLD_PERCENT} AS DOUBLE) AS high_threshold_percent,
        '{sql_string(NOTIFICATION_TARGET_TYPE)}' AS notification_target_type,
        '{sql_string(NOTIFICATION_TARGET_VALUE)}' AS notification_target_value,
        {str(IS_ACTIVE).lower()} AS is_active
    """


print("Phase 003 - Setup Monitoring Rules")
print("Serverless only. This notebook writes only agent_rules configuration.")
print("Out of scope: no CDF read, no source update, no events, no alerts, no notification rows, no Genie, no LLM.")
print(f"RULES_TABLE = {RULES_TABLE}")
print(f"RULE_ID = {RULE_ID}")
print(f"SOURCE_TABLE = {SOURCE_TABLE}")
print(f"BUSINESS_KEY_COLUMNS = {BUSINESS_KEY_COLUMNS}")
print(f"CONTEXT_COLUMNS = {CONTEXT_COLUMNS}")
print(f"WATCHED_COLUMN = {WATCHED_COLUMN}")
print(f"MEDIUM_THRESHOLD_PERCENT = {MEDIUM_THRESHOLD_PERCENT}")
print(f"HIGH_THRESHOLD_PERCENT = {HIGH_THRESHOLD_PERCENT}")

# COMMAND ----------

run_sql(
    "Ensure agent_rules table exists",
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
).collect()

describe_df = run_sql("Describe agent_rules table", f"DESCRIBE TABLE {RULES_TABLE}")
expected_columns = {
    "rule_id": "string",
    "rule_name": "string",
    "catalog_name": "string",
    "schema_name": "string",
    "table_name": "string",
    "business_key_columns": "string",
    "context_columns": "string",
    "watched_column": "string",
    "condition_type": "string",
    "medium_threshold_percent": "double",
    "high_threshold_percent": "double",
    "notification_target_type": "string",
    "notification_target_value": "string",
    "is_active": "boolean",
    "created_at": "timestamp",
    "updated_at": "timestamp",
}
actual_columns = {
    row.col_name: row.data_type.lower()
    for row in describe_df.collect()
    if row.col_name in expected_columns
}
missing_columns = sorted(set(expected_columns) - set(actual_columns))
if missing_columns:
    raise RuntimeError(f"agent_rules table missing expected columns: {missing_columns}")

wrong_types = {
    column_name: {"expected": expected_type, "actual": actual_columns[column_name]}
    for column_name, expected_type in expected_columns.items()
    if actual_columns.get(column_name) != expected_type
}
if wrong_types:
    raise RuntimeError(f"agent_rules table columns have unexpected types: {wrong_types}")

print(f"[OK] {RULES_TABLE} exists with the expected Phase 003 schema.")

# COMMAND ----------

before_count = scalar(
    f"""
    SELECT COUNT(*)
    FROM {RULES_TABLE}
    WHERE rule_id = '{sql_string(RULE_ID)}'
    """
)
print(f"[MERGE] {RULE_ID} rows before merge = {before_count}")
if before_count > 1:
    raise RuntimeError(
        f"Refusing to merge {RULE_ID}: expected at most 1 pre-existing row, found {before_count}"
    )

run_sql(
    "Merge SALES_PRICE_CHANGE_001 into agent_rules",
    f"""
    MERGE INTO {RULES_TABLE} AS target
    USING ({rule_literal_select()}) AS source
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
    )
    """,
).collect()

after_count = scalar(
    f"""
    SELECT COUNT(*)
    FROM {RULES_TABLE}
    WHERE rule_id = '{sql_string(RULE_ID)}'
    """
)
inserted_count = 1 if before_count == 0 and after_count == 1 else 0
updated_count = 1 if before_count >= 1 and after_count == before_count else 0
print(f"[MERGE] {RULE_ID} rows after merge = {after_count}")
print(f"[MERGE] inserted = {inserted_count}, updated = {updated_count}")

# COMMAND ----------

active_rule_df = run_sql(
    "Display active SALES_PRICE_CHANGE_001 rule",
    f"""
    SELECT
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
    FROM {RULES_TABLE}
    WHERE rule_id = '{sql_string(RULE_ID)}'
      AND is_active = true
    ORDER BY updated_at DESC
    """,
)
display(active_rule_df)

# COMMAND ----------

failures = []

total_count = scalar(
    f"""
    SELECT COUNT(*)
    FROM {RULES_TABLE}
    WHERE rule_id = '{sql_string(RULE_ID)}'
    """
)
if total_count != 1:
    failures.append(f"expected exactly 1 row for {RULE_ID}, found {total_count}")

active_count = scalar(
    f"""
    SELECT COUNT(*)
    FROM {RULES_TABLE}
    WHERE rule_id = '{sql_string(RULE_ID)}'
      AND is_active = true
    """
)
if active_count != 1:
    failures.append(f"expected 1 active rule, found {active_count}")

rule_rows = active_rule_df.collect()
if len(rule_rows) == 1:
    row = rule_rows[0]
    expected_values = {
        "is_active": IS_ACTIVE,
        "catalog_name": SOURCE_CATALOG,
        "schema_name": SOURCE_SCHEMA,
        "table_name": SOURCE_TABLE_NAME,
        "business_key_columns": BUSINESS_KEY_COLUMNS,
        "context_columns": CONTEXT_COLUMNS,
        "watched_column": WATCHED_COLUMN,
        "condition_type": CONDITION_TYPE,
        "notification_target_type": NOTIFICATION_TARGET_TYPE,
        "notification_target_value": NOTIFICATION_TARGET_VALUE,
    }

    for field_name, expected_value in expected_values.items():
        actual_value = getattr(row, field_name)
        if actual_value != expected_value:
            failures.append(f"{field_name} expected {expected_value}, found {actual_value}")

    if float(row.medium_threshold_percent) != float(MEDIUM_THRESHOLD_PERCENT):
        failures.append(
            f"medium_threshold_percent expected {MEDIUM_THRESHOLD_PERCENT}, found {row.medium_threshold_percent}"
        )
    if float(row.high_threshold_percent) != float(HIGH_THRESHOLD_PERCENT):
        failures.append(
            f"high_threshold_percent expected {HIGH_THRESHOLD_PERCENT}, found {row.high_threshold_percent}"
        )

    resolved_source_table = f"{row.catalog_name}.{row.schema_name}.{row.table_name}"
    if resolved_source_table != SOURCE_TABLE:
        failures.append(f"source table expected {SOURCE_TABLE}, found {resolved_source_table}")
else:
    failures.append(f"expected 1 active rule row to validate, found {len(rule_rows)}")

if failures:
    failure_message = "FAILED: " + "; ".join(failures)
    print(failure_message)
    raise RuntimeError(failure_message)

print(f"SUCCESS: {RULE_ID} is active with the expected configuration.")
