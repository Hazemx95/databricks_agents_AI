# Databricks CDF Agent Monitoring

Phase 000 bootstraps a Databricks CDF rule-based monitoring project for a single source table. It creates local project structure, reusable SQL scripts, a Databricks-compatible bootstrap notebook, project constants, placeholder modules, placeholder notebooks, and minimal tests.

Full roadmap: [PLAN.md](PLAN.md).

## First Scope

- Source table: `databricks_arrow_cata.bronz.sales_info`
- Monitoring schema: `databricks_arrow_cata.monitoring`
- First watched column: `sls_price`
- First key column: `sls_ord_num`
- First rule ID: `SALES_PRICE_CHANGE_001`

## Environment

This project starts in Databricks Free Edition and assumes serverless compute only. Phase 000 does not require classic clusters, secrets, external APIs, Genie, LangChain, OpenAI, RAG, email, Teams, Slack, or webhooks.

## Project Structure

- `PLAN.md`: Full multi-phase roadmap.
- `sql/`: Databricks SQL scripts for source discovery and monitoring table DDL.
- `notebooks/`: Databricks Python source notebooks.
- `src/cdf_agent_monitoring/`: Python package constants and future-phase placeholders.
- `tests/`: Local pytest checks that do not require Spark.
- `docs/`: Project documentation placeholder.
- `config/`: Configuration placeholder for future phases.

## Phase 000 Execution

1. Sync or upload this repository to Databricks.
2. Open `notebooks/00_project_bootstrap.py` in Databricks.
3. Attach serverless compute.
4. Run the notebook.
5. Confirm the monitoring schema and tables exist.
6. Confirm source table schema, detail, properties, history, sample rows, and CDF status are displayed.

The notebook is idempotent. It uses `CREATE SCHEMA IF NOT EXISTS` and `CREATE TABLE IF NOT EXISTS` for monitoring objects.

## Phase 000 Out Of Scope

- Enabling Change Data Feed.
- Updating the source table.
- Calling `table_changes()`.
- Running CDF detection.
- Running rule-based agent logic.
- Creating alert or notification records.
- Genie enrichment.
- LangChain, OpenAI, RAG, or external LLM usage.
- External email, Teams, Slack, or webhook delivery.

## Phase 001 Execution

1. Sync or upload this repository to Databricks.
2. Open `notebooks/01_enable_cdf_and_validate.py` in Databricks.
3. Attach serverless compute.
4. Run all cells, top to bottom.

The notebook enables CDF on `databricks_arrow_cata.bronz.sales_info` if needed, captures a baseline table version, applies one controlled `sls_price * 1.15` update for `sls_ord_num = 'SO43697'`, and validates that CDF returns both `update_preimage` and `update_postimage` rows. It prints a rollback SQL suggestion but does not execute rollback automatically.

## Troubleshooting

- If the source table cannot be described, confirm read access to `databricks_arrow_cata.bronz.sales_info`.
- If the monitoring schema cannot be created, confirm create permissions in catalog `databricks_arrow_cata`.
- If serverless compute is unavailable, resolve workspace compute access before running Phase 000.

## Local Validation

```bash
python -m pytest
```

The local tests validate imports and constants only. They do not require Spark or Databricks.
