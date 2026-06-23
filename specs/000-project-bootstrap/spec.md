# Feature Specification: Project Bootstrap (Phase 000)

**Feature Branch**: `feature/000-project-bootstrap`

**Created**: 2026-06-20

**Status**: Draft

**Input**: Phase 000 requirements from PLAN.md and project constitution

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initialize Project Structure (Priority: P1)

As a **data engineer**, I want to **set up the local project directory structure** so that **all code, scripts, and documentation follow a consistent organization and can be version-controlled**.

**Why this priority**: P1 — Project structure is the foundation for all subsequent phases; without it, team members cannot collaborate effectively or locate artifacts.

**Independent Test**: Can be fully tested by verifying that all required directories exist with proper names and organization, the PLAN.md is preserved, and README.md is present with clear instructions.

**Acceptance Scenarios**:

1. **Given** an empty project directory, **When** I run the bootstrap process, **Then** the following directory structure exists:
   - `specs/` (for feature specifications)
   - `sql/` (for SQL scripts)
   - `notebooks/` (for Databricks notebooks)
   - `src/` (for Python source code)
   - `docs/` (for documentation)
   - `config/` (for configuration files)

2. **Given** the project structure is created, **When** I review the README, **Then** it contains clear instructions for running Phase 000 and dependencies (Databricks workspace access, serverless compute).

3. **Given** PLAN.md already exists in the project, **When** the bootstrap runs, **Then** PLAN.md remains unchanged and is not overwritten.

---

### User Story 2 - Discover and Validate Source Table (Priority: P1)

As a **data engineer**, I want to **query the source table to confirm it exists, is Delta format, and document its schema** so that **I can verify the data is accessible and baseline its properties before enabling CDF**.

**Why this priority**: P1 — Source table validation is critical to confirm the environment is correctly configured before Phase 001 proceeds with CDF enablement.

**Independent Test**: Can be fully tested by running discovery queries and confirming output shows table exists, is Delta, includes expected columns, and CDF is currently disabled.

**Acceptance Scenarios**:

1. **Given** I have Databricks workspace access and serverless compute is available, **When** I run the discovery queries, **Then** the source table `databricks_arrow_cata.bronz.sales_info` exists and is queryable.

2. **Given** the source table exists, **When** I run `DESCRIBE DETAIL`, **Then** the output confirms the table format is "delta" and includes all expected columns (sls_ord_num, sls_prd_key, sls_cust_id, sls_price, etc.).

3. **Given** the source table exists, **When** I run `SHOW TBLPROPERTIES`, **Then** the output includes the current table properties and confirms `delta.enableChangeDataFeed` is not yet set or is false.

4. **Given** the discovery queries succeed, **When** I sample rows from the source table, **Then** I can see at least 1 row with real data in the expected columns.

---

### User Story 3 - Create Monitoring Schema and Tables (Priority: P1)

As a **data engineer**, I want to **create the monitoring schema and all required Delta tables** so that **Phase 001 and later phases have the table structure to write CDF events, alerts, and notifications**.

**Why this priority**: P1 — The monitoring tables are a prerequisite for all downstream phases; without them, the workflow cannot store results.

**Independent Test**: Can be fully tested by verifying that all five required tables exist in the monitoring schema, are Delta format, have the correct schema structure, and can accept writes.

**Acceptance Scenarios**:

1. **Given** the monitoring schema does not yet exist, **When** I run the schema creation script, **Then** the schema `databricks_arrow_cata.monitoring` is created.

2. **Given** the schema exists, **When** I run the table creation script, **Then** the following tables are created as managed Delta tables:
   - `agent_rules` (with columns: rule_id, rule_name, catalog_name, schema_name, table_name, business_key_columns, context_columns, watched_column, condition_type, medium_threshold_percent, high_threshold_percent, notification_target_type, notification_target_value, is_active, created_at, updated_at)
   - `change_events` (with columns: event_id, rule_id, event_type, source_table, business_key_json, old_value, new_value, change_percent, context_json, commit_version, commit_timestamp, created_at)
   - `agent_alerts` (with columns: alert_id, event_id, rule_id, severity, should_notify, reason, recommended_action, agent_type, alert_status, genie_context_json, created_at, updated_at)
   - `notification_log` (with columns: notification_id, alert_id, rule_id, notification_type, subject, body, delivery_status, created_at, sent_at)
   - `agent_run_log` (with columns: run_id, phase, status, message, row_count, created_at, completed_at)

3. **Given** the tables are created, **When** I run a test insert, **Then** a row can be written to each table without error.

4. **Given** I run the table creation script a second time, **Then** the script completes without error (idempotent — no duplicate tables created).

---

## Functional Requirements

### FR-1: Project Folder Structure

The project must include the following directory structure, each with clear purpose:

- **`specs/`** — Feature specifications and related artifacts
- **`sql/`** — SQL scripts for source discovery, table creation, and monitoring queries
- **`notebooks/`** — Databricks notebooks for interactive execution and testing
- **`src/`** — Python source code for utility functions and agent logic
- **`docs/`** — Project documentation, guides, and architecture notes
- **`config/`** — Configuration files (constants, environment-specific settings)

### FR-2: README and Documentation

Create `README.md` at project root with:

- Brief project description (Databricks CDF rule-based monitoring workflow)
- Phase 000 goal and scope
- Prerequisites (Databricks workspace, serverless compute, catalog access)
- Instructions to run Phase 000 bootstrap (e.g., "Upload notebook to Databricks and run in serverless compute")
- Link to PLAN.md for full implementation roadmap
- List of first project constants (SOURCE_TABLE, MONITORING_SCHEMA, etc.)

### FR-3: Requirements File

Create `requirements.txt` with Python dependencies:

- databricks-sql-connector (for SQL operations from Python)
- Any other standard packages needed for Phase 000 utilities

### FR-4: SQL Discovery Scripts

Create SQL scripts in `sql/` directory:

- **`00-source-discovery.sql`** — Queries to inspect source table:
  - `DESCRIBE TABLE databricks_arrow_cata.bronz.sales_info;`
  - `DESCRIBE DETAIL databricks_arrow_cata.bronz.sales_info;`
  - `SHOW TBLPROPERTIES databricks_arrow_cata.bronz.sales_info;`
  - `DESCRIBE HISTORY databricks_arrow_cata.bronz.sales_info LIMIT 10;`
  - `SELECT COUNT(*) FROM databricks_arrow_cata.bronz.sales_info;`
  - Sample query: `SELECT sls_ord_num, sls_price, sls_prd_key, sls_cust_id FROM databricks_arrow_cata.bronz.sales_info LIMIT 10;`

- **`01-create-monitoring-schema.sql`** — Creates the monitoring schema if not exists:
  - `CREATE SCHEMA IF NOT EXISTS databricks_arrow_cata.monitoring;`

- **`02-create-monitoring-tables.sql`** — Creates all five monitoring Delta tables with proper schemas and `IF NOT EXISTS` clauses to ensure idempotency

### FR-5: Databricks Notebook

Create `notebooks/00-bootstrap.py` (Databricks Python notebook) that:

- Defines project constants (SOURCE_TABLE, MONITORING_SCHEMA, RULE_ID, etc.)
- **Validates preconditions** (source table exists, catalog access available, sufficient permissions) and **fails fast with clear error messages** if any precondition is missing
- Runs source discovery queries and displays results
- Creates monitoring schema
- Creates all monitoring tables with explicit primary key and composite uniqueness constraints (see Key Entities section)
- **Logs human-readable progress** for each operation: schema creation, table creation, discovery queries (e.g., "✓ Source table validated", "✓ Monitoring schema created", "✓ 5 tables created"); provide summary at end
- Supports re-execution without error (idempotent)

### FR-6: Project Constants

All scripts must use these constants defined at the top of the notebook/script:

```python
SOURCE_TABLE = "databricks_arrow_cata.bronz.sales_info"
MONITORING_SCHEMA = "databricks_arrow_cata.monitoring"
RULE_ID = "SALES_PRICE_CHANGE_001"
BUSINESS_KEY_COLUMNS = ["sls_ord_num"]
CONTEXT_COLUMNS = ["sls_prd_key", "sls_cust_id", "sls_quantity", "sls_sales"]
WATCHED_COLUMN = "sls_price"
MEDIUM_THRESHOLD_PERCENT = 5.0
HIGH_THRESHOLD_PERCENT = 10.0
```

### FR-7: Idempotency

All SQL and Python code must be safe to re-run:

- Use `CREATE ... IF NOT EXISTS` for schema and table creation
- No `DROP TABLE` or destructive operations in Phase 000
- If monitoring table already exists, skip creation without error
- If schema already exists, skip creation without error

### FR-8: CDF Status Documentation

The notebook must:

- Query and display the current value of `delta.enableChangeDataFeed` property on the source table
- Document the baseline CDF status (disabled or enabled)
- **Do NOT enable CDF** — CDF enablement is Phase 001 work
- **Do NOT modify the source table** in any way

### FR-9: Execution Environment

All scripts must work in:

- Databricks Free Edition workspace
- Serverless compute only (no classic clusters)
- Python 3.x runtime
- SQL notebook environment

## Success Criteria

1. **Project structure created**: All required directories (specs/, sql/, notebooks/, src/, docs/, config/) exist with README.md at root
2. **Source table validated**: Discovery queries confirm source table is Delta, exists, is queryable, contains expected columns, and CDF is not yet enabled
3. **Monitoring schema created**: Schema `databricks_arrow_cata.monitoring` exists and is accessible
4. **All monitoring tables created**: agent_rules, change_events, agent_alerts, notification_log, and agent_run_log exist as Delta tables with correct schemas and explicit primary key / composite uniqueness constraints
5. **Constants defined**: Project constants are centralized and use correct table/column names from the source table
6. **Idempotency verified**: Bootstrap notebook can be run twice without error or duplicate objects
7. **Documentation complete**: README.md contains clear instructions, prerequisites, and links to PLAN.md
8. **No CDF changes**: Source table is not modified; CDF property remains in its initial state
9. **Error handling implemented**: Bootstrap notebook validates preconditions (source table exists, permissions available) and fails fast with clear, actionable error messages if any precondition is missing
10. **Logging implemented**: Bootstrap notebook prints human-readable progress (checkmark + message for each operation; summary at end); quiet on success
11. **Scripts execute successfully**: All SQL and Python scripts run without error in serverless environment
12. **No external dependencies**: Phase 000 has no email, Teams, Slack, webhook, LangChain, OpenAI, or RAG dependencies

## Key Entities

### Source Table: sales_info

- **Full name**: `databricks_arrow_cata.bronz.sales_info`
- **Format**: Delta
- **Columns**: sls_ord_num, sls_prd_key, sls_cust_id, sls_order_dt, sls_ship_dt, sls_due_dt, sls_sales, sls_quantity, sls_price, _rescued_data, _source_file_path, _source_file_name, _source_file_size, _source_file_modification_time, _ingest_ts, _source_system, _source_schema, _source_table

### Monitoring Schema

- **Full name**: `databricks_arrow_cata.monitoring`
- **Purpose**: Hosts all monitoring tables for alert generation, notifications, and audit logs

### Monitoring Tables

#### agent_rules

**Purpose**: Store rule definitions for monitoring events.

**Columns**:
- `rule_id` STRING — PRIMARY KEY, e.g., "SALES_PRICE_CHANGE_001"
- `rule_name` STRING (NOT NULL)
- `catalog_name` STRING (NOT NULL)
- `schema_name` STRING (NOT NULL)
- `table_name` STRING (NOT NULL)
- `business_key_columns` STRING (NOT NULL, comma-separated)
- `context_columns` STRING (NOT NULL, comma-separated)
- `watched_column` STRING (NOT NULL)
- `condition_type` STRING (NOT NULL), e.g., "percent_change"
- `medium_threshold_percent` DECIMAL (NOT NULL)
- `high_threshold_percent` DECIMAL (NOT NULL)
- `notification_target_type` STRING (NOT NULL)
- `notification_target_value` STRING (NOT NULL)
- `is_active` BOOLEAN (NOT NULL, default true)
- `created_at` TIMESTAMP (NOT NULL)
- `updated_at` TIMESTAMP (NOT NULL)

**Constraints**: `rule_id` is PRIMARY KEY; ensures one rule definition per rule_id.

---

#### change_events

**Purpose**: Store structured events from CDF change detection (populated in Phase 002+).

**Columns**:
- `event_id` STRING — PRIMARY KEY, unique identifier
- `rule_id` STRING (NOT NULL) — FOREIGN KEY to agent_rules
- `event_type` STRING (NOT NULL), e.g., "SALES_PRICE_CHANGE"
- `source_table` STRING (NOT NULL)
- `business_key_json` STRING (NOT NULL, JSON format)
- `old_value` STRING
- `new_value` STRING
- `change_percent` DECIMAL
- `context_json` STRING (JSON format)
- `commit_version` LONG (NOT NULL)
- `commit_timestamp` TIMESTAMP (NOT NULL)
- `created_at` TIMESTAMP (NOT NULL)

**Constraints**: `event_id` is PRIMARY KEY. Composite unique constraint on (rule_id, business_key_json, watched_column, commit_version) to prevent duplicate event detection.

---

#### agent_alerts

**Purpose**: Store rule-based agent decisions and alert metadata.

**Columns**:
- `alert_id` STRING — PRIMARY KEY, unique identifier
- `event_id` STRING (NOT NULL) — FOREIGN KEY to change_events
- `rule_id` STRING (NOT NULL) — FOREIGN KEY to agent_rules
- `severity` STRING (NOT NULL), one of: "HIGH", "MEDIUM", "LOW"
- `should_notify` BOOLEAN (NOT NULL)
- `reason` STRING (NOT NULL)
- `recommended_action` STRING
- `agent_type` STRING (NOT NULL), e.g., "RULE_BASED_AGENT"
- `alert_status` STRING (NOT NULL), e.g., "CREATED", "NOTIFICATION_LOGGED"
- `genie_context_json` STRING (optional, JSON format, added in Phase 007)
- `created_at` TIMESTAMP (NOT NULL)
- `updated_at` TIMESTAMP (NOT NULL)

**Constraints**: `alert_id` is PRIMARY KEY. Composite unique constraint on (event_id, rule_id) to prevent duplicate alerts for the same event.

---

#### notification_log

**Purpose**: Store notification records (in Phase 000-006, audit-table-only; Phase 008 adds external delivery).

**Columns**:
- `notification_id` STRING — PRIMARY KEY, unique identifier
- `alert_id` STRING (NOT NULL) — FOREIGN KEY to agent_alerts
- `rule_id` STRING (NOT NULL) — FOREIGN KEY to agent_rules
- `notification_type` STRING (NOT NULL), e.g., "ALERT_TABLE_ONLY"
- `subject` STRING
- `body` STRING (NOT NULL)
- `delivery_status` STRING (NOT NULL), e.g., "LOGGED", "SENT", "FAILED"
- `created_at` TIMESTAMP (NOT NULL)
- `sent_at` TIMESTAMP (optional, set when delivered)

**Constraints**: `notification_id` is PRIMARY KEY.

---

#### agent_run_log

**Purpose**: Log workflow execution traces and status for audit and debugging.

**Columns**:
- `run_id` STRING — PRIMARY KEY, unique identifier per execution
- `phase` STRING (NOT NULL), e.g., "000", "001", "002"
- `status` STRING (NOT NULL), one of: "STARTED", "IN_PROGRESS", "COMPLETED", "FAILED"
- `message` STRING (optional, error or summary message)
- `row_count` LONG (optional, count of rows created/processed)
- `created_at` TIMESTAMP (NOT NULL)
- `completed_at` TIMESTAMP (optional, set when phase completes)

**Constraints**: `run_id` is PRIMARY KEY.

## Assumptions

1. **Databricks workspace access** is available and user has create/write permissions on catalog `databricks_arrow_cata`
2. **Source table exists** at `databricks_arrow_cata.bronz.sales_info` and contains real sales data
3. **Serverless compute is available** in the workspace and can be used for notebook execution
4. **No custom classic clusters** are required or used in Phase 000
5. **Delta Change Data Feed** is not yet enabled on the source table (will be enabled in Phase 001)
6. **Python 3.x runtime** is available in Databricks notebooks
7. **SQL notebook environment** supports standard Databricks SQL syntax
8. **Git folder integration** is available in Databricks workspace for version control (optional but recommended)

## Clarifications

### Session 2026-06-20

- Q1: What should the bootstrap notebook do when preconditions fail (source table missing, permissions denied)? → A: Fail fast with clear error messages, providing troubleshooting guidance instead of attempting creates
- Q2: Should monitoring tables have explicit primary key and uniqueness constraints? → C: Use composite keys for deduplication (rule_id PK on agent_rules; alert_id PK on agent_alerts with composite unique on event_id + rule_id; unique constraints on change_events to prevent duplicate detections)
- Q3: What logging format and verbosity should the bootstrap notebook use? → B: Human-readable progress (print status for each operation like "✓ Source table validated"; summary at end; quiet on success)

## Out of Scope

- Enabling Change Data Feed (deferred to Phase 001)
- Running CDF detection or `table_changes()` queries
- Updating the source table with test data
- Rule-based agent logic or alert generation
- External notifications (email, Teams, Slack, webhook)
- Genie AI context enrichment
- LangChain, OpenAI API, RAG, or any external LLM
- Production deployment or scheduling

## Acceptance Criteria Summary

- [ ] Project structure created with all required directories
- [ ] README.md and requirements.txt exist
- [ ] Source discovery SQL scripts exist and are executable
- [ ] Schema creation SQL script exists and is idempotent
- [ ] Monitoring table creation SQL script exists and is idempotent
- [ ] Databricks bootstrap notebook exists and can be uploaded to workspace
- [ ] Bootstrap notebook creates monitoring schema and tables successfully
- [ ] Bootstrap notebook displays source table schema, detail, properties, history, and sample rows
- [ ] All project constants are defined with correct source table and column names
- [ ] CDF status is documented but not changed
- [ ] No external dependencies (email, webhook, LLM, RAG)
- [ ] Scripts execute without error in serverless compute environment
