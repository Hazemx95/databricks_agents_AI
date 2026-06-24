# Quickstart: Monitoring Rules Table (Phase 003)

Validates that the first monitoring rule `SALES_PRICE_CHANGE_001` is stored and active in `databricks_arrow_cata.monitoring.agent_rules`, idempotently.

## Prerequisites

- Databricks Free Edition, serverless compute, DEFAULT `.databrickscfg` profile (or the configured Databricks MCP server).
- Phase 000 complete — `monitoring` schema and `agent_rules` table exist. *(Verified live: the table exists with 16 columns and currently 0 rows.)*

## Files

- `sql/002_create_agent_rules.sql` — table DDL (`CREATE TABLE IF NOT EXISTS`) + reference `MERGE` upsert.
- `notebooks/03_setup_monitoring_rules.py` — setup + validation notebook.
- `src/cdf_agent_monitoring/config.py` — rule constants (single source of truth).

## Run

1. Import/open `notebooks/03_setup_monitoring_rules.py` in the workspace (or run via Jobs) on serverless.
2. Run all cells.

## Expected outcome (first run)

- Notebook prints the Phase 003 title and constants.
- `MERGE` reports: before = 0, inserted = 1, after = 1.
- The active rule row is displayed with the canonical values (see [data-model.md](./data-model.md)).
- Final line: `SUCCESS: SALES_PRICE_CHANGE_001 is active with the expected configuration.`

## Expected outcome (re-run — idempotency)

- `MERGE` reports: before = 1, inserted = 0 (matched → updated in place), after = 1.
- Row count for `SALES_PRICE_CHANGE_001` stays exactly 1.
- Final line: `SUCCESS` again.

## Manual verification (SQL)

```sql
SELECT rule_id, is_active, watched_column, business_key_columns,
       medium_threshold_percent, high_threshold_percent,
       catalog_name, schema_name, table_name,
       notification_target_type, notification_target_value
FROM databricks_arrow_cata.monitoring.agent_rules
WHERE rule_id = 'SALES_PRICE_CHANGE_001';

-- Idempotency: must return exactly 1
SELECT COUNT(*) AS active_count
FROM databricks_arrow_cata.monitoring.agent_rules
WHERE rule_id = 'SALES_PRICE_CHANGE_001' AND is_active = true;
```

Expected: one active row; `watched_column = sls_price`, `business_key_columns = sls_ord_num`, thresholds `5.0` / `10.0`, source resolves to `databricks_arrow_cata.bronz.sales_info`, notification target `alert_table` / `databricks_arrow_cata.monitoring.notification_log`.

## Definition of done (FR-013)

Phase 003 is successful only when the **live** `agent_rules` table holds exactly one active `SALES_PRICE_CHANGE_001` row matching the canonical values — demonstrated by the displayed row and the `active_count = 1` query. Not successful from local code generation alone.

## Out of scope

No CDF read, no source update, no event/alert/notification creation, no Genie/LLM.
