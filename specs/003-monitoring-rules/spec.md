# Feature Specification: Monitoring Rules Table (Phase 003)

**Feature Branch**: `003-monitoring-rules`

**Created**: 2026-06-24

**Status**: Implemented

**Input**: Phase 003 requirements from PLAN.md and project constitution

## Overview

Phases 000–002 created the monitoring schema and tables, enabled Change Data Feed, and produced structured change events. Until now, the rule that defines *what* to watch (source table, business key, watched column, severity thresholds, notification target) lives only as hardcoded constants in code.

Phase 003 moves that configuration into data. It validates that `databricks_arrow_cata.monitoring.agent_rules` exists, then inserts (upserts) the first monitoring rule — `SALES_PRICE_CHANGE_001` — into that table using an idempotent `MERGE`, so the downstream workflow can load rule configuration dynamically instead of relying on hardcoded business logic. The phase finishes by validating the persisted rule against the expected source table and columns, displaying the active rule, and printing a clear SUCCESS or FAILED status.

This phase stops at **storing and validating the rule**. It does not read CDF, does not build events, does not classify severity, and does not create alerts or notifications — those belong to other phases.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm the Rules Table Exists (Priority: P1)

As a **data engineer**, I want to **confirm that `databricks_arrow_cata.monitoring.agent_rules` exists with the expected structure** so that **the rule can be stored in a known, stable location before the workflow depends on it**.

**Why this priority**: P1 — Every later action writes to this table. If it is missing or malformed, nothing downstream can load a rule. Confirming it first prevents writing into a non-existent or wrong-shaped target.

**Independent Test**: Can be fully tested by checking that the `agent_rules` table is present in the `monitoring` schema and exposes the rule-configuration columns (`rule_id`, `rule_name`, `catalog_name`, `schema_name`, `table_name`, `business_key_columns`, `context_columns`, `watched_column`, `condition_type`, `medium_threshold_percent`, `high_threshold_percent`, `notification_target_type`, `notification_target_value`, `is_active`).

**Acceptance Scenarios**:

1. **Given** the monitoring schema exists, **When** the notebook checks for `agent_rules`, **Then** it confirms the table is present before attempting any write.
2. **Given** the `agent_rules` table is present, **When** the notebook inspects it, **Then** it confirms the rule-configuration columns required to store `SALES_PRICE_CHANGE_001` are available.
3. **Given** the `agent_rules` table is missing, **When** the notebook starts, **Then** it reports that precondition failure clearly and does not attempt to upsert the rule.

---

### User Story 2 - Upsert the First Rule Idempotently (Priority: P1)

As a **data engineer**, I want to **insert the first monitoring rule into `agent_rules` using a `MERGE` keyed on `rule_id`** so that **the rule is created once and re-running the notebook never duplicates it**.

**Why this priority**: P1 — Storing the rule is the core deliverable of this phase, and idempotency is a constitutional requirement (Principle IV). A duplicate rule would make "the active rule" ambiguous for every downstream phase.

**Independent Test**: Can be fully tested by running the upsert once and confirming exactly one row exists for `SALES_PRICE_CHANGE_001`, then running it again and confirming the row count for that `rule_id` is still exactly one.

**Acceptance Scenarios**:

1. **Given** no row exists for `SALES_PRICE_CHANGE_001`, **When** the upsert runs, **Then** a single new rule row is inserted with all configured values.
2. **Given** a row already exists for `SALES_PRICE_CHANGE_001`, **When** the upsert runs again, **Then** no duplicate row is created; the existing row is matched on `rule_id` and updated in place.
3. **Given** the upsert is run twice, **When** counting rows for `SALES_PRICE_CHANGE_001` after the second run, **Then** the count is exactly one.
4. **Given** the rule is inserted, **When** the row is written, **Then** `is_active` is `true` and the audit timestamps (`created_at`, `updated_at`) are populated.

---

### User Story 3 - Validate the Stored Rule Against Expected Configuration (Priority: P1)

As a **data engineer**, I want to **validate that the persisted rule's values match the expected source table and columns** so that **the workflow loads a rule that actually points at the real data it must monitor**.

**Why this priority**: P1 — A stored rule with wrong values is worse than no rule: the workflow would silently monitor the wrong table or column. Validation is what makes the rule trustworthy.

**Independent Test**: Can be fully tested by reading back the single active `SALES_PRICE_CHANGE_001` row and asserting each field equals its expected value (source table parts, business key, watched column, thresholds, notification target, active flag).

**Acceptance Scenarios**:

1. **Given** the rule is stored, **When** I read it back, **Then** exactly one *active* rule exists for `SALES_PRICE_CHANGE_001`.
2. **Given** the stored rule, **When** I check its target, **Then** `catalog_name` = `databricks_arrow_cata`, `schema_name` = `bronz`, and `table_name` = `sales_info`, together resolving to `databricks_arrow_cata.bronz.sales_info`.
3. **Given** the stored rule, **When** I check its monitored columns, **Then** `business_key_columns` = `sls_ord_num`, `watched_column` = `sls_price`, and `context_columns` = `sls_prd_key,sls_cust_id,sls_quantity,sls_sales`.
4. **Given** the stored rule, **When** I check its thresholds and type, **Then** `condition_type` = `percent_change`, `medium_threshold_percent` = `5.0`, and `high_threshold_percent` = `10.0`.
5. **Given** the stored rule, **When** I check its notification target, **Then** `notification_target_type` = `alert_table` and `notification_target_value` = `databricks_arrow_cata.monitoring.notification_log`.
6. **Given** any expected value does not match, **When** validation runs, **Then** the notebook reports which field failed and prints a FAILED status.

---

### User Story 4 - Display the Rule and Print Clear Status (Priority: P2)

As a **data engineer**, I want the notebook to **display the active rule and print an unambiguous SUCCESS or FAILED status** so that **I can visually confirm the rule is correct and safe to re-run**.

**Why this priority**: P2 — Observability is required (Principle V), but the display/status is supporting evidence around the core upsert/validation logic rather than the deliverable itself.

**Independent Test**: Can be fully tested by running the notebook and confirming it shows the active `SALES_PRICE_CHANGE_001` row and prints exactly one terminal status line — SUCCESS when all validations pass, FAILED otherwise.

**Acceptance Scenarios**:

1. **Given** the notebook runs to completion, **When** validation finishes, **Then** it displays the active rule row for `SALES_PRICE_CHANGE_001`.
2. **Given** all validations pass, **When** the notebook finishes, **Then** it prints a clear SUCCESS status.
3. **Given** any validation fails (table missing, duplicate rule, or mismatched value), **When** the notebook finishes, **Then** it prints a clear FAILED status that identifies the failure.

---

### Edge Cases

- **Rules table missing**: The notebook fails fast with a clear message and does not attempt the upsert.
- **Re-running the notebook**: The upsert is idempotent — the second run leaves exactly one row for `SALES_PRICE_CHANGE_001` with no duplicates.
- **Pre-existing rule with stale/wrong values**: The `MERGE` updates the matched row to the expected values so the stored rule converges to the canonical configuration.
- **More than one row for the rule_id**: If validation finds more than one (active) row for `SALES_PRICE_CHANGE_001`, it is treated as a failure and reported.
- **Inactive rule**: If the only `SALES_PRICE_CHANGE_001` row has `is_active = false`, the "exactly one active rule" check fails and the notebook prints FAILED.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow MUST verify that `databricks_arrow_cata.monitoring.agent_rules` exists before attempting to write, and report a clear failure if it does not.
- **FR-002**: A SQL script (`sql/002_create_agent_rules.sql`) MUST define the `agent_rules` table structure so the rules table can be (re)created idempotently.
- **FR-003**: The workflow MUST upsert the first rule into `agent_rules` using a `MERGE` keyed on `rule_id`, so the operation is idempotent and re-running it does not create duplicates.
- **FR-004**: The upserted rule MUST populate every configured field: `rule_id` = `SALES_PRICE_CHANGE_001`, `rule_name` = `Sales price change monitoring`, `catalog_name` = `databricks_arrow_cata`, `schema_name` = `bronz`, `table_name` = `sales_info`, `business_key_columns` = `sls_ord_num`, `context_columns` = `sls_prd_key,sls_cust_id,sls_quantity,sls_sales`, `watched_column` = `sls_price`, `condition_type` = `percent_change`, `medium_threshold_percent` = `5.0`, `high_threshold_percent` = `10.0`, `notification_target_type` = `alert_table`, `notification_target_value` = `databricks_arrow_cata.monitoring.notification_log`, `is_active` = `true`.
- **FR-005**: The upsert MUST populate the audit timestamps (`created_at` on insert, `updated_at` on insert and on update).
- **FR-006**: The workflow MUST validate that exactly one *active* rule exists for `SALES_PRICE_CHANGE_001` after the upsert.
- **FR-007**: The workflow MUST validate that the stored rule's values match the expected source table and columns (catalog/schema/table, business key, watched column, context columns, condition type, thresholds, and notification target).
- **FR-008**: The notebook MUST display the active `SALES_PRICE_CHANGE_001` rule row.
- **FR-009**: The notebook MUST print a single, unambiguous terminal status — SUCCESS when all validations pass, FAILED (identifying the failing check) otherwise.
- **FR-010**: Rule field values MUST come from the shared constants in `src/cdf_agent_monitoring/config.py` where those constants already exist (e.g., `RULE_ID`, business key, context columns, watched column, thresholds, table names), rather than being independently re-hardcoded; any new constants needed for Phase 003 MAY be added there.
- **FR-011**: The workflow MUST NOT read CDF, MUST NOT modify the source table, MUST NOT create event JSON, MUST NOT run rule-based classification, and MUST NOT create alerts or notification-log rows.
- **FR-012**: The workflow MUST run on Databricks serverless compute only, with no external network calls, no hardcoded secrets, and no Genie/LangChain/OpenAI/RAG/external-LLM dependencies.
- **FR-013**: Phase 003 MUST be validated against the live Databricks workspace (via the configured Databricks MCP server or the DEFAULT `.databrickscfg` profile); it MUST NOT be marked successful from local code generation alone.

### Key Entities *(include if feature involves data)*

- **Monitoring Rule**: A configuration record in `databricks_arrow_cata.monitoring.agent_rules` describing one monitored event type. Key attributes: identity (`rule_id`, `rule_name`); source target (`catalog_name`, `schema_name`, `table_name`); monitored columns (`business_key_columns`, `context_columns`, `watched_column`); evaluation behavior (`condition_type`, `medium_threshold_percent`, `high_threshold_percent`); notification routing (`notification_target_type`, `notification_target_value`); lifecycle (`is_active`, `created_at`, `updated_at`). Uniquely identified by `rule_id`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After running the notebook, the `agent_rules` table contains exactly one active row for `SALES_PRICE_CHANGE_001`.
- **SC-002**: Every field of the stored rule equals its expected value — source resolves to `databricks_arrow_cata.bronz.sales_info`, business key is `sls_ord_num`, watched column is `sls_price`, medium threshold is `5.0`, high threshold is `10.0`, and notification target is `databricks_arrow_cata.monitoring.notification_log`.
- **SC-003**: Re-running the notebook adds zero new rows for `SALES_PRICE_CHANGE_001` (100% idempotent), verified by an unchanged count of exactly one.
- **SC-004**: The notebook always terminates with an unambiguous status — SUCCESS when all validations pass, FAILED otherwise — for both the pass and fail cases.
- **SC-005**: The downstream workflow can load the rule's configuration from `agent_rules` (by `rule_id`) without reading any hardcoded business logic.
- **SC-006**: Phase 003 success is demonstrated against the live Databricks workspace, with the active rule row shown as evidence.

## Assumptions

- **Table pre-created**: The `agent_rules` table was created in Phase 000 and its schema (16 columns, primary key on `rule_id`) is reused as-is; Phase 003 confirms its existence and writes into it. `sql/002_create_agent_rules.sql` already defines this structure and is treated as the create/update script for the rules table.
- **Single rule scope**: Only `SALES_PRICE_CHANGE_001` is created in this phase; multi-rule and multi-table monitoring are out of scope.
- **`schema_name` semantics**: `schema_name` in the rule (`bronz`) refers to the *source* schema of the monitored table, not the monitoring schema — consistent with PLAN.md and the constitution.
- **Column-list format**: `business_key_columns` and `context_columns` are stored as comma-separated strings (no spaces), matching the existing schema and PLAN.md values.
- **Threshold precision**: `medium_threshold_percent` and `high_threshold_percent` are stored as doubles (`5.0`, `10.0`).
- **Shared constants reused**: Rule values are sourced from `src/cdf_agent_monitoring/config.py` where available, keeping code and stored rule in agreement.
- **MERGE key**: Idempotency uses `rule_id` as the `MERGE` match key, since `rule_id` is the table's primary key.

## Out of Scope

- Reading the Change Data Feed.
- Updating or modifying the source table.
- Creating change-event JSON or writing to `change_events`.
- Running the rule-based agent or classifying severity (HIGH/MEDIUM/LOW).
- Creating alerts, notification-log rows, or any notification.
- Using Genie, LangChain, OpenAI, RAG, or any external LLM.
- Sending external notifications (email/Teams/Slack/webhook).

## Dependencies

- **Phase 000** — monitoring schema and `agent_rules` table exist.
- **Shared config** — `src/cdf_agent_monitoring/config.py` provides the canonical rule constants.
- **Databricks workspace** — reachable via the configured Databricks MCP server or DEFAULT `.databrickscfg` profile, serverless compute available.

## Required Files

- `sql/002_create_agent_rules.sql` — create/update script for the `agent_rules` table (already present; confirm it matches the rule schema).
- `notebooks/03_setup_monitoring_rules.py` — notebook that confirms the table, upserts the first rule via `MERGE`, validates it, displays the active rule, and prints SUCCESS/FAILED.
- `src/cdf_agent_monitoring/config.py` — only if new shared constants are needed for the rule (e.g., `RULE_NAME`, `CONDITION_TYPE`, `NOTIFICATION_TARGET_*`).
- `README.md` — only if Phase 003 execution notes are needed.
