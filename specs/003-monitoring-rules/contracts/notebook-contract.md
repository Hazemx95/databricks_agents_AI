# Contract: `notebooks/03_setup_monitoring_rules.py`

Serverless Databricks notebook. Sets up and validates the first monitoring rule. **Read-only** with respect to CDF and the source table; the only write is the `agent_rules` upsert.

## Inputs

- Shared constants from `src/cdf_agent_monitoring/config.py` (notebook adds `src/` to `sys.path`, mirroring notebooks 01/02).
- No widgets are exposed because the rule configuration is fixed.

## Behavior (ordered stages)

1. **Header & title** — `# Databricks notebook source` header; print `Phase 003 - Setup Monitoring Rules` and the key constants (`RULES_TABLE`, `RULE_ID`, target source table, thresholds). State serverless-only and that no CDF/source write occurs.
2. **Define rule constants** — assemble the 14 business column values from `config.py` (join list constants into comma-separated strings).
3. **Ensure table exists** — run `CREATE TABLE IF NOT EXISTS ... agent_rules (...)` (same DDL as `sql/002_create_agent_rules.sql`) so the notebook is self-contained and safe to rerun. If the table cannot be confirmed/created, fail clearly.
4. **MERGE the rule** — execute the upsert per [agent-rules-merge.md](./agent-rules-merge.md), keyed on `rule_id`. Report rows before/after and inserted/updated.
5. **Display active rule** — `display()` the row(s) where `rule_id = 'SALES_PRICE_CHANGE_001' AND is_active = true`.
6. **Validate** — run checks V1–V11 from [data-model.md](../data-model.md); collect failure reasons.
7. **Print status** — exactly one terminal line: `SUCCESS` if zero failures, else `FAILED: <semicolon-separated reasons>`.

## Output contract

- Always displays the active rule row (when the table exists).
- Prints **exactly one** of:
  - `SUCCESS: SALES_PRICE_CHANGE_001 is active with the expected configuration.`
  - `FAILED: <reasons>` (e.g., `FAILED: expected 1 active rule, found 0; high_threshold_percent != 10.0`).
- Re-running yields `SUCCESS` again with the rule count still exactly 1 (idempotent).

## Guarantees / Non-goals

- MUST NOT read CDF, MUST NOT query or modify `bronz.sales_info`, MUST NOT write to `change_events`, `agent_alerts`, `notification_log`, or `agent_run_log`.
- MUST NOT use Genie/LangChain/OpenAI/RAG or any external network call.
- MUST run on serverless; no secrets.
- The only side effect is the single-row upsert into `agent_rules`.

## Validation status mapping

| Check | Failure message fragment |
|-------|--------------------------|
| V1 table exists | `agent_rules table not found` |
| V2 exactly one active | `expected 1 active rule, found <n>` |
| V3 is_active | `is_active is not true` |
| V4 watched_column | `watched_column != sls_price` |
| V5 business_key_columns | `business_key_columns != sls_ord_num` |
| V6 context_columns | `context_columns mismatch` |
| V7 medium threshold | `medium_threshold_percent != 5.0` |
| V8 high threshold | `high_threshold_percent != 10.0` |
| V9 source parts | `source table != databricks_arrow_cata.bronz.sales_info` |
| V10 condition_type | `condition_type != percent_change` |
| V11 notification target | `notification target mismatch` |
