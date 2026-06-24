# Databricks notebook source
# Phase 002 - Run CDF Detection

from pathlib import Path
import sys

from pyspark.sql import functions as F

PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "src").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cdf_agent_monitoring import event_builder

SOURCE_TABLE = "databricks_arrow_cata.bronz.sales_info"
EVENTS_TABLE = "databricks_arrow_cata.monitoring.change_events"
RULE_ID = "SALES_PRICE_CHANGE_001"
EVENT_TYPE = "SALES_PRICE_CHANGE"
BUSINESS_KEY_COLUMNS = ["sls_ord_num"]
CONTEXT_COLUMNS = ["sls_prd_key", "sls_cust_id", "sls_quantity", "sls_sales"]
WATCHED_COLUMN = "sls_price"


def sql_string(value):
    return str(value).replace("'", "''")


def run_sql(label, sql_text):
    print(f"[RUN] {label}")
    result = spark.sql(sql_text)
    print(f"[OK] {label}")
    return result


def get_widget_value(name, default_value):
    try:
        dbutils.widgets.text(name, default_value)
        return dbutils.widgets.get(name).strip()
    except NameError:
        return default_value


def get_cdf_status():
    properties_df = run_sql("Show source table properties", f"SHOW TBLPROPERTIES {SOURCE_TABLE}")
    display(properties_df)
    cdf_rows = [row for row in properties_df.collect() if row.key == "delta.enableChangeDataFeed"]
    return cdf_rows[0].value if cdf_rows else "not set"


def detect_cdf_start_version():
    history_df = run_sql(
        "Detect CDF enablement version",
        f"DESCRIBE HISTORY {SOURCE_TABLE}",
    )
    history_rows = (
        history_df.filter(
            (F.col("operation") == "SET TBLPROPERTIES")
            & F.col("operationParameters")["properties"].contains("delta.enableChangeDataFeed")
            & F.col("operationParameters")["properties"].contains("true")
        )
        .orderBy(F.col("version").asc())
        .limit(1)
        .collect()
    )
    if history_rows:
        return str(history_rows[0].version)
    return "0"


print("Phase 002 - Run CDF Detection")
print("Serverless only. This notebook reads CDF and writes change_events; it does not update the source table.")
print(f"SOURCE_TABLE = {SOURCE_TABLE}")
print(f"EVENTS_TABLE = {EVENTS_TABLE}")
print(f"RULE_ID = {RULE_ID}")
print(f"BUSINESS_KEY_COLUMNS = {BUSINESS_KEY_COLUMNS}")
print(f"CONTEXT_COLUMNS = {CONTEXT_COLUMNS}")
print(f"WATCHED_COLUMN = {WATCHED_COLUMN}")

# COMMAND ----------

cdf_status = get_cdf_status()
print(f"[CDF] delta.enableChangeDataFeed = {cdf_status}")
if str(cdf_status).lower() != "true":
    raise RuntimeError(
        f"CDF is not enabled on {SOURCE_TABLE}. Phase 002 does not enable CDF; run Phase 001 first."
    )

# COMMAND ----------

start_version = get_widget_value("start_version", "")
end_version = get_widget_value("end_version", "")

if not start_version:
    start_version = detect_cdf_start_version()
    print(f"[VERSIONS] start_version was blank; using detected CDF start version {start_version}.")

print(f"[VERSIONS] start_version = {start_version}")
print(f"[VERSIONS] end_version = {end_version or '(latest)'}")

table_name_literal = sql_string(SOURCE_TABLE)
if end_version:
    cdf_sql = f"SELECT * FROM table_changes('{table_name_literal}', {int(start_version)}, {int(end_version)})"
else:
    cdf_sql = f"SELECT * FROM table_changes('{table_name_literal}', {int(start_version)})"

raw_cdf_df = run_sql("Read raw CDF rows", cdf_sql)
display(raw_cdf_df)

# COMMAND ----------

old_df = (
    raw_cdf_df.filter(F.col("_change_type") == "update_preimage")
    .select(
        F.col("sls_ord_num"),
        F.col(WATCHED_COLUMN).alias("old_value_raw"),
        F.col("_commit_version").alias("commit_version"),
    )
)

new_df = (
    raw_cdf_df.filter(F.col("_change_type") == "update_postimage")
    .select(
        F.col("sls_ord_num"),
        F.col(WATCHED_COLUMN).alias("new_value_raw"),
        F.col("_commit_version").alias("commit_version"),
        F.col("_commit_timestamp").alias("commit_timestamp"),
        *[F.col(column) for column in CONTEXT_COLUMNS],
    )
)

paired_df = old_df.join(new_df, on=["sls_ord_num", "commit_version"], how="inner")
display(paired_df)
print(f"[PAIRING] paired update_preimage/update_postimage rows = {paired_df.count()}")

# COMMAND ----------

changed_df = paired_df.filter(~F.col("old_value_raw").eqNullSafe(F.col("new_value_raw")))

business_key_struct = F.struct(*[F.col(column).cast("string").alias(column) for column in BUSINESS_KEY_COLUMNS])
context_struct = F.struct(*[F.col(column).cast("string").alias(column) for column in CONTEXT_COLUMNS])
change_percent_udf = F.udf(event_builder.calculate_change_percent, "double")

events_df = changed_df.select(
    F.expr("uuid()").alias("event_id"),
    F.lit(RULE_ID).alias("rule_id"),
    F.lit(EVENT_TYPE).alias("event_type"),
    F.lit(SOURCE_TABLE).alias("source_table"),
    F.to_json(business_key_struct).alias("business_key_json"),
    F.col("old_value_raw").cast("string").alias("old_value"),
    F.col("new_value_raw").cast("string").alias("new_value"),
    change_percent_udf(F.col("old_value_raw"), F.col("new_value_raw")).alias(
        "change_percent"
    ),
    F.to_json(context_struct).alias("context_json"),
    F.lit(WATCHED_COLUMN).alias("watched_column"),
    F.col("commit_version").cast("bigint").alias("commit_version"),
    F.col("commit_timestamp").alias("commit_timestamp"),
    F.current_timestamp().alias("created_at"),
)

display(events_df)
detected_event_count = events_df.count()
print(f"[DETECTION] detected sls_price change events = {detected_event_count}")

# COMMAND ----------

before_count = spark.table(EVENTS_TABLE).filter(F.col("rule_id") == RULE_ID).count()
print(f"[MERGE] existing {RULE_ID} events before merge = {before_count}")

if detected_event_count > 0:
    events_df.createOrReplaceTempView("phase002_change_events")

    run_sql(
        "Merge detected events into change_events",
        f"""
        MERGE INTO {EVENTS_TABLE} AS target
        USING phase002_change_events AS source
        ON target.rule_id = source.rule_id
          AND target.business_key_json = source.business_key_json
          AND target.watched_column = source.watched_column
          AND target.commit_version = source.commit_version
        WHEN NOT MATCHED THEN INSERT (
          event_id,
          rule_id,
          event_type,
          source_table,
          business_key_json,
          old_value,
          new_value,
          change_percent,
          context_json,
          watched_column,
          commit_version,
          commit_timestamp,
          created_at
        ) VALUES (
          source.event_id,
          source.rule_id,
          source.event_type,
          source.source_table,
          source.business_key_json,
          source.old_value,
          source.new_value,
          source.change_percent,
          source.context_json,
          source.watched_column,
          source.commit_version,
          source.commit_timestamp,
          source.created_at
        )
        """,
    ).collect()
else:
    print("[MERGE] No detected price changes to merge.")

after_count = spark.table(EVENTS_TABLE).filter(F.col("rule_id") == RULE_ID).count()
inserted_count = after_count - before_count
print(f"[MERGE] existing {RULE_ID} events after merge = {after_count}")
print(f"[MERGE] inserted events = {inserted_count}")

# COMMAND ----------

final_events_df = run_sql(
    "Display final change_events rows",
    f"""
    SELECT
      event_id,
      rule_id,
      event_type,
      source_table,
      business_key_json,
      old_value,
      new_value,
      change_percent,
      context_json,
      watched_column,
      commit_version,
      commit_timestamp,
      created_at
    FROM {EVENTS_TABLE}
    WHERE rule_id = '{sql_string(RULE_ID)}'
    ORDER BY commit_version, business_key_json
    """,
)
display(final_events_df)

if inserted_count > 0:
    print(f"SUCCESS: CDF price-change detection wrote {inserted_count} new event(s) to {EVENTS_TABLE}.")
else:
    print(
        "NO_NEW_EVENTS: No new CDF sls_price changes were inserted. "
        "Either no price changes were present in the selected window or all detected changes already existed."
    )
