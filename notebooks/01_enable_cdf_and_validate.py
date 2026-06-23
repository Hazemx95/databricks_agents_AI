# Databricks notebook source
# Phase 001 - Enable and Validate Change Data Feed

from pathlib import Path

PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "src").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

SQL_DIR = PROJECT_ROOT / "sql"

SOURCE_TABLE = "databricks_arrow_cata.bronz.sales_info"
TEST_ORDER_NUMBER = "SO43697"
WATCHED_COLUMN = "sls_price"


def sql_string(literal_text):
    return str(literal_text).replace("'", "''")


def run_sql(label, sql_text):
    print(f"[RUN] {label}")
    result = spark.sql(sql_text)
    print(f"[OK] {label}")
    return result


def get_cdf_status():
    properties_df = run_sql("Show table properties", f"SHOW TBLPROPERTIES {SOURCE_TABLE}")
    display(properties_df)

    cdf_rows = [row for row in properties_df.collect() if row.key == "delta.enableChangeDataFeed"]
    return cdf_rows[0].value if cdf_rows else "not set"


def first_update_metric(update_df, metric_name):
    update_rows = update_df.collect()
    if not update_rows:
        return None

    update_metrics = update_rows[0].asDict()
    return update_metrics.get(metric_name)


print("Phase 001 - Enable and Validate Change Data Feed")
print("Serverless compute only. This notebook runs one controlled UPDATE and does not auto-rollback.")
print(f"SOURCE_TABLE = {SOURCE_TABLE}")
print(f"TEST_ORDER_NUMBER = {TEST_ORDER_NUMBER}")
print(f"WATCHED_COLUMN = {WATCHED_COLUMN}")

# COMMAND ----------

detail_df = run_sql("Describe source detail", f"DESCRIBE DETAIL {SOURCE_TABLE}")
display(detail_df)

detail_rows = detail_df.collect()
if not detail_rows:
    raise RuntimeError(f"DESCRIBE DETAIL returned no rows for {SOURCE_TABLE}.")

table_format = detail_rows[0].asDict().get("format")
if str(table_format).lower() != "delta":
    raise RuntimeError(
        f"Source table {SOURCE_TABLE} must be Delta before CDF can be enabled. Current format: {table_format}."
    )

print(f"[OK] Source table format is Delta: {SOURCE_TABLE}")

# COMMAND ----------

cdf_status_before = get_cdf_status()
print(f"[CDF] delta.enableChangeDataFeed before = {cdf_status_before}")

if str(cdf_status_before).lower() != "true":
    enable_sql = (SQL_DIR / "007_enable_cdf.sql").read_text()
    run_sql("Enable CDF", enable_sql).collect()
else:
    print("[CDF] CDF is already enabled; skipping ALTER TABLE.")

cdf_status_after = get_cdf_status()
print(f"[CDF] delta.enableChangeDataFeed after = {cdf_status_after}")

if str(cdf_status_after).lower() != "true":
    raise RuntimeError(f"CDF was not enabled on {SOURCE_TABLE}. Final status: {cdf_status_after}")

# COMMAND ----------

history_df = run_sql("Capture baseline table version", f"DESCRIBE HISTORY {SOURCE_TABLE} LIMIT 1")
display(history_df)

history_rows = history_df.collect()
if not history_rows:
    raise RuntimeError(f"DESCRIBE HISTORY returned no rows for {SOURCE_TABLE}.")

baseline_version = history_rows[0].version
print(f"[BASELINE] baseline_version = {baseline_version}")

# COMMAND ----------

order_filter = f"sls_ord_num = '{sql_string(TEST_ORDER_NUMBER)}'"
before_df = run_sql(
    "Read test row before update",
    f"""
    SELECT *
    FROM {SOURCE_TABLE}
    WHERE {order_filter}
    """,
)
display(before_df)

before_rows = before_df.collect()
if not before_rows:
    print(f"[RESULT] status=FAILED reason=No row found for sls_ord_num={TEST_ORDER_NUMBER} before update.")
    raise RuntimeError(f"Cannot validate CDF because {TEST_ORDER_NUMBER} was not found in {SOURCE_TABLE}.")

old_price = before_rows[0][WATCHED_COLUMN]
print(f"[BEFORE] {TEST_ORDER_NUMBER} {WATCHED_COLUMN} = {old_price}")

# COMMAND ----------

update_df = run_sql(
    "Run controlled price update",
    f"""
    UPDATE {SOURCE_TABLE}
    SET {WATCHED_COLUMN} = {WATCHED_COLUMN} * 1.15
    WHERE sls_ord_num = '{sql_string(TEST_ORDER_NUMBER)}'
    """,
)

num_affected_rows = first_update_metric(update_df, "num_affected_rows")
print(f"[UPDATE] num_affected_rows = {num_affected_rows}")
if num_affected_rows != 1:
    print(f"[WARN] Expected exactly 1 affected row for {TEST_ORDER_NUMBER}; got {num_affected_rows}.")

# COMMAND ----------

after_df = run_sql(
    "Read test row after update",
    f"""
    SELECT *
    FROM {SOURCE_TABLE}
    WHERE {order_filter}
    """,
)
display(after_df)

after_rows = after_df.collect()
if not after_rows:
    print(f"[RESULT] status=FAILED reason=No row found for sls_ord_num={TEST_ORDER_NUMBER} after update.")
    raise RuntimeError(f"Cannot validate CDF because {TEST_ORDER_NUMBER} was not found after update.")

new_price = after_rows[0][WATCHED_COLUMN]
print(f"[AFTER] {TEST_ORDER_NUMBER} {WATCHED_COLUMN} = {new_price}")

# COMMAND ----------

changes_df = run_sql(
    "Read CDF rows for test order",
    f"""
    SELECT
      sls_ord_num,
      sls_prd_key,
      sls_cust_id,
      sls_sales,
      sls_quantity,
      sls_price,
      _change_type,
      _commit_version,
      _commit_timestamp
    FROM table_changes('{SOURCE_TABLE}', {baseline_version})
    WHERE sls_ord_num = '{sql_string(TEST_ORDER_NUMBER)}'
    ORDER BY _commit_version, _change_type
    """,
)
display(changes_df)

change_rows = changes_df.collect()
preimage_rows = [row for row in change_rows if row._change_type == "update_preimage"]
postimage_rows = [row for row in change_rows if row._change_type == "update_postimage"]

has_preimage = bool(preimage_rows)
has_postimage = bool(postimage_rows)

cdf_old_price = preimage_rows[-1].sls_price if has_preimage else None
cdf_new_price = postimage_rows[-1].sls_price if has_postimage else None
change_commit_version = postimage_rows[-1]._commit_version if has_postimage else None

print(f"[CDF] update_preimage exists = {has_preimage}")
print(f"[CDF] update_postimage exists = {has_postimage}")
print(f"[CDF] old {WATCHED_COLUMN} from preimage = {cdf_old_price}")
print(f"[CDF] new {WATCHED_COLUMN} from postimage = {cdf_new_price}")
print(f"[CDF] change_commit_version = {change_commit_version}")

if has_preimage and has_postimage:
    print(
        f"[RESULT] status=SUCCESS old_price={old_price} new_price={new_price} "
        f"commit_version={change_commit_version}"
    )
else:
    missing = []
    if not has_preimage:
        missing.append("update_preimage")
    if not has_postimage:
        missing.append("update_postimage")
    print(
        f"[RESULT] status=FAILED reason=Missing {', '.join(missing)} for {TEST_ORDER_NUMBER} "
        f"from baseline_version={baseline_version}."
    )

# COMMAND ----------

print("[ROLLBACK SUGGESTION] Not executed automatically. Review before running manually:")
print(
    f"""
UPDATE {SOURCE_TABLE}
SET {WATCHED_COLUMN} = {WATCHED_COLUMN} / 1.15
WHERE sls_ord_num = '{sql_string(TEST_ORDER_NUMBER)}';
""".strip()
)
