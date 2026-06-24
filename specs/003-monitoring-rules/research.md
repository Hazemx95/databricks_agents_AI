# Phase 0 Research: Monitoring Rules Table (Phase 003)

All unknowns are resolved; no `NEEDS CLARIFICATION` remain. The table structure and live state were verified against the workspace before planning.

## R1. Does the rules table already exist, and with what schema?

- **Decision**: Reuse the existing `databricks_arrow_cata.monitoring.agent_rules` table as-is; do not alter its schema.
- **Rationale**: Verified live via `information_schema.columns` — the table exists with the exact 16 columns expected (`rule_id`, `rule_name`, `catalog_name`, `schema_name`, `table_name`, `business_key_columns`, `context_columns`, `watched_column`, `condition_type`, `medium_threshold_percent DOUBLE`, `high_threshold_percent DOUBLE`, `notification_target_type`, `notification_target_value`, `is_active BOOLEAN`, `created_at TIMESTAMP`, `updated_at TIMESTAMP`). It currently holds **0 rows**. `sql/002_create_agent_rules.sql` already defines this DDL with `CREATE TABLE IF NOT EXISTS` and a `PRIMARY KEY (rule_id) NOT ENFORCED`.
- **Alternatives considered**: Recreating/altering the table — rejected (out of scope, and unnecessary since it already matches).

## R2. Insert vs. upsert — how to make rule creation idempotent?

- **Decision**: `MERGE INTO ... AS target USING (one-row source) AS source ON target.rule_id = source.rule_id`, with `WHEN MATCHED THEN UPDATE SET` (all business columns + `updated_at`) and `WHEN NOT MATCHED THEN INSERT` (all columns, `created_at`/`updated_at` = `current_timestamp()`).
- **Rationale**: Matches the project's established idempotency pattern (notebook 02 uses `MERGE` for events). Keying on the PK `rule_id` guarantees re-runs keep exactly one row (SC-001/SC-003) and converge any stale values to canonical (Edge: pre-existing wrong values). Constitution IV requires idempotent writes.
- **Alternatives considered**: `INSERT ... WHERE NOT EXISTS` (would not fix stale values on re-run); `INSERT OVERWRITE` (would wipe other rules — unsafe for future multi-rule); plain `INSERT` (creates duplicates). All rejected.

## R3. Where do the rule values come from?

- **Decision**: Define the rule values once in `src/cdf_agent_monitoring/config.py` and reference them from the notebook. Reuse existing constants (`RULE_ID`, `BUSINESS_KEY_COLUMNS`, `CONTEXT_COLUMNS`, `WATCHED_COLUMN`, `MEDIUM_THRESHOLD_PERCENT`, `HIGH_THRESHOLD_PERCENT`, `RULES_TABLE`, `NOTIFICATION_LOG_TABLE`); add the missing ones: `RULE_NAME`, `EVENT_TYPE`, `CONDITION_TYPE`, `NOTIFICATION_TARGET_TYPE`, `NOTIFICATION_TARGET_VALUE`, and source-table parts (`SOURCE_CATALOG`, `SOURCE_SCHEMA`, `SOURCE_TABLE_NAME`).
- **Rationale**: FR-010 and SC-005 require the rule to be defined once and readable by Phase 004 (as a fallback). Single source of truth prevents drift between code and the stored row. The column-list strings are produced by `",".join(BUSINESS_KEY_COLUMNS)` etc.
- **Alternatives considered**: Hardcoding values directly in the notebook — rejected (duplicates constants, risks drift). A separate YAML/JSON config file — rejected (overkill for one rule; `config.py` already exists and is imported elsewhere).

## R4. `schema_name` semantics — source schema or monitoring schema?

- **Decision**: Store `schema_name = 'bronz'` (the *source* schema of the monitored table).
- **Rationale**: PLAN.md and the constitution both specify `schema_name: bronz` / `table_name: sales_info`, which combine with `catalog_name: databricks_arrow_cata` to resolve to the monitored table `databricks_arrow_cata.bronz.sales_info`. The monitoring schema (`monitoring`) is where the *rules table* lives, not what the rule points at.
- **Alternatives considered**: Storing `monitoring` — rejected (would misdirect Phase 004 to the wrong table).

## R5. Column-list storage format.

- **Decision**: Comma-separated strings with no spaces: `business_key_columns = 'sls_ord_num'`, `context_columns = 'sls_prd_key,sls_cust_id,sls_quantity,sls_sales'`.
- **Rationale**: Matches PLAN.md values and the existing STRING columns; downstream phases split on `,`.
- **Alternatives considered**: JSON arrays or `ARRAY<STRING>` — rejected (columns are STRING in the existing schema; no schema change allowed).

## R6. Notebook validation strategy and status output.

- **Decision**: Assertion-style validation collecting failure reasons, then a single terminal print: `SUCCESS` if no failures, else `FAILED: <reasons>`. Checks: table exists; exactly one active row for `SALES_PRICE_CHANGE_001`; `is_active = true`; `watched_column = sls_price`; `business_key_columns = sls_ord_num`; `medium_threshold_percent = 5.0`; `high_threshold_percent = 10.0`; source parts resolve to `databricks_arrow_cata.bronz.sales_info`; `condition_type = percent_change`; notification target = `alert_table` / `databricks_arrow_cata.monitoring.notification_log`.
- **Rationale**: FR-006–FR-009, SC-002/SC-004 require explicit, field-level validation and an unambiguous status. Collecting all reasons (rather than failing on the first) gives a complete diagnosis in one run.
- **Alternatives considered**: Raising on first failure — rejected (less informative); silent display only — rejected (FR-009 requires a printed status).

## R7. Which notebook filename?

- **Decision**: Create `notebooks/03_setup_monitoring_rules.py` (new). Leave the existing `notebooks/03_run_rule_based_agent.py` stub for Phase 004.
- **Rationale**: The spec/brief name the deliverable `03_setup_monitoring_rules.py`; "setup" describes this phase (populate config) versus Phase 004's "run" (apply rules). Keeps phase boundaries clean.
- **Alternatives considered**: `03_run_monitoring_rules.py` — acceptable per the brief but "setup" is clearer for a config-population step; reusing the Phase 004 stub — rejected (different responsibility).
