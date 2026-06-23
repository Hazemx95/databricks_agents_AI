# Contract: `notebooks/02_run_cdf_detection.py`

Databricks serverless notebook. Detect `sls_price` changes from CDF and persist structured events. **Never** enables CDF, mutates the source, classifies severity, or writes alerts/notifications.

## Header & constants

- First line: `# Databricks notebook source`
- Title comment: `# Phase 002 - Run CDF Detection`
- Add `src/` to `sys.path` (mirror notebook 01) and import `config`, `event_builder`. Constants (sourced from `config.py`, shown here for reference):
  - `SOURCE_TABLE = "databricks_arrow_cata.bronz.sales_info"`
  - `EVENTS_TABLE = "databricks_arrow_cata.monitoring.change_events"`
  - `RULE_ID = "SALES_PRICE_CHANGE_001"`
  - `EVENT_TYPE = "SALES_PRICE_CHANGE"`
  - `BUSINESS_KEY_COLUMNS = ["sls_ord_num"]`
  - `CONTEXT_COLUMNS = ["sls_prd_key", "sls_cust_id", "sls_quantity", "sls_sales"]`
  - `WATCHED_COLUMN = "sls_price"`

## Behavioral steps (in order)

1. **Validate CDF**: `SHOW TBLPROPERTIES {SOURCE_TABLE}`. If `delta.enableChangeDataFeed` is not `true`, print a clear failure and stop (raise) — do not read the feed. *(Confirmed live = true.)*
2. **Version inputs**: widgets `start_version` (default `"0"`) and `end_version` (default `""`). Print the selected versions. If `end_version` is empty, read from `start_version` to latest.
3. **Read CDF**: `table_changes(SOURCE_TABLE, start, end)` (or `readChangeFeed` reader). `display(...)` the raw CDF rows.
4. **Pair rows**: filter `update_preimage` (old) and `update_postimage` (new); inner-join on `sls_ord_num` AND `_commit_version`. `display(...)` the paired rows.
5. **Detect changes**: keep pairs where old `sls_price` != new `sls_price`; compute `change_percent` (via `event_builder.calculate_change_percent`).
6. **Build events**: produce rows with exactly the 13 `change_events` columns (see data-model.md). `event_id` unique per change; `business_key_json` / `context_json` via the helpers; `created_at = current_timestamp()`. `display(...)` the built event rows. *(Helper columns like `business_key`/`change_type` may exist on the working frame but are NOT written.)*
7. **Write events**: register a temp view and run a single `MERGE INTO {EVENTS_TABLE}` with
   `ON rule_id, business_key_json, watched_column, commit_version` and `WHEN NOT MATCHED THEN INSERT` (insert-only).
8. **Validate output**: `display(...)` final `change_events` rows where `rule_id = 'SALES_PRICE_CHANGE_001'`.
9. **Status**:
   - If new events were inserted → print a clear `SUCCESS` message including the count of new events.
   - If no `sls_price` change exists, or all detected changes already existed → print a clear **no-new-events** message (not an error, not a misleading success).

## Idempotency

Re-running over the same version window MUST insert zero new rows (verified by unchanged `change_events` count and no duplicate dedup keys).

## Guardrails

- Serverless only; no secrets; no external network; no Genie/LLM/LangChain/OpenAI/RAG.
- No `ALTER`, no `UPDATE`/`INSERT`/`DELETE` against the source table.
- No writes to `agent_alerts`, `notification_log`, or `agent_run_log`.
