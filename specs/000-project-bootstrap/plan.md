# Implementation Plan: Project Bootstrap (Phase 000)

**Branch**: `feature/000-project-bootstrap` | **Date**: 2026-06-20 | **Spec**: [specs/000-project-bootstrap/spec.md](spec.md)

**Input**: Feature specification from `/specs/000-project-bootstrap/spec.md`

## Summary

Phase 000 bootstraps the Databricks CDF Rule-Based AI Agent Monitoring project by creating the local project structure, setting up monitoring schema and tables, and validating the source table schema and Delta format. This phase establishes the foundation for later phases (Phase 001 enables CDF, Phase 002 detects changes, Phase 003+ implements rule-based alerting).

**Technical Approach**: Create local directory structure with Python/SQL scripts, define project constants in centralized config module, build Databricks Python notebook that:
1. Validates preconditions (source table exists, permissions available, serverless compute)
2. Runs source table discovery queries and displays results
3. Creates monitoring schema and 5 managed Delta tables with explicit primary keys and composite uniqueness constraints
4. Logs human-readable progress and fails fast with clear error messages if preconditions fail

**Why This Approach**: Databricks Free Edition enforces serverless-only compute; local files remain Git-friendly and syncable to Databricks Git folders. SQL scripts are reusable across phases. Centralized config enables single-source-of-truth for table/column names.

## Technical Context

**Language/Version**: Python 3.x (Databricks notebook runtime) with SQL (Databricks SQL)

**Primary Dependencies**:
- `databricks-sql-connector` (for SQL operations from Python scripts)
- `pytest` (for unit tests of utility functions; no Spark dependency for Phase 000)

**Storage**: Databricks Unity Catalog and Delta tables
- Catalog: `databricks_arrow_cata`
- Source schema: `bronz`
- Source table: `databricks_arrow_cata.bronz.sales_info` (existing Delta table, pre-populated)
- Monitoring schema: `databricks_arrow_cata.monitoring` (created by Phase 000)

**Testing**: pytest (unit tests only; integration tests with Databricks deferred to Phase 002+)

**Target Platform**: Databricks Free Edition workspace, serverless compute only (no classic clusters)

**Project Type**: Data monitoring / agentic workflow (CLI-style Databricks notebook + SQL scripts)

**Performance Goals**: 
- Source table discovery: <5 seconds (reads schema metadata, not full table scan)
- Monitoring table creation: <30 seconds (DDL only, idempotent)
- Bootstrap notebook end-to-end: <1 minute on serverless compute

**Constraints**:
- Free Edition serverless only (no classic clusters, no hardcoded secrets)
- No external API calls in Phase 000 (email, Teams, Slack, LangChain, OpenAI deferred)
- Idempotent SQL: `CREATE ... IF NOT EXISTS` only; no `DROP TABLE`
- Fail fast on precondition failures (source table missing, permissions denied, catalog not accessible)

**Scale/Scope**:
- Single catalog (databricks_arrow_cata), single source table (sales_info)
- 5 monitoring tables with modest schema (15-20 columns each, no initial rows)
- First rule definition: SALES_PRICE_CHANGE_001 (percent-change detection)
- ~200 lines of bootstrap notebook code, ~500 lines of SQL DDL

## Constitution Check

**Gate: Must pass before Phase 0 research. Verified below.**

**Constitution**: [.specify/memory/constitution.md](.specify/memory/constitution.md)

### Core Principles Alignment

✅ **Principle I: Free Edition / Serverless Constraints**
- Phase 000 uses serverless compute only; no classic clusters or external APIs
- Plan specifies Databricks Free Edition, serverless notebooks, no hardcoded secrets
- Passes ✓

✅ **Principle II: Delta Change Data Feed (CDF) Events**
- Phase 000 validates source table is Delta format but does NOT enable CDF (Phase 001 work)
- Plan explicitly defers CDF enablement with phase001/sql/007_enable_cdf.sql outside the Phase 000 execution path
- Passes ✓

✅ **Principle III: Rule-Based Agent (No LLM in POC)**
- Phase 000 does not implement rule-based logic (Phase 004 work); stores rule definition only
- Plan has no LangChain, OpenAI, RAG, or external LLM calls
- Passes ✓

✅ **Principle IV: Data Safety & Idempotency**
- All SQL scripts use `CREATE ... IF NOT EXISTS` (idempotent, safe to re-run)
- Composite unique constraints defined on agent_alerts, change_events to prevent duplicates
- No destructive operations (`DROP TABLE`) in Phase 000
- Passes ✓

✅ **Principle V: Audit & Observability**
- agent_run_log table created to store execution traces and status
- Bootstrap notebook logs human-readable progress for each operation
- All table operations timestamped with created_at, updated_at
- Passes ✓

**Gate Result**: ✅ **PASS** — All 5 core principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/000-project-bootstrap/
├── spec.md              # Feature specification (input)
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 research findings (generated below)
├── data-model.md        # Phase 1 data model (generated below)
├── quickstart.md        # Phase 1 validation guide (generated below)
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── contracts/           # Phase 1 (none for Phase 000 — internal only)
```

### Source Code (repository root)

```text
databricks_agents_AI/
├── PLAN.md                          # Original roadmap (unchanged)
├── README.md                        # Project overview (NEW)
├── requirements.txt                 # Python dependencies (NEW)
├── sql/
│   ├── 000_describe_source_table.sql        # Source discovery queries (NEW)
│   ├── 001_create_monitoring_schema.sql     # Monitoring schema DDL (NEW)
│   ├── 002_create_agent_rules.sql           # agent_rules table (NEW)
│   ├── 003_create_change_events.sql         # change_events table (NEW)
│   ├── 004_create_agent_alerts.sql          # agent_alerts table (NEW)
│   ├── 005_create_notification_log.sql      # notification_log table (NEW)
│   └── 006_create_agent_run_log.sql         # agent_run_log table (NEW)
├── phase001/
│   └── sql/
│       └── 007_enable_cdf.sql               # CDF enablement (Phase 001 only)
├── notebooks/
│   ├── 00_project_bootstrap.py              # Phase 000 bootstrap (NEW, MAIN)
│   ├── 01_enable_cdf_and_validate.py        # Phase 001 placeholder (NEW, TODO)
│   ├── 02_run_cdf_detection.py              # Phase 002 placeholder (NEW, TODO)
│   ├── 03_run_rule_based_agent.py           # Phase 003/004 placeholder (NEW, TODO)
│   ├── 04_write_notification_log.py         # Phase 005 placeholder (NEW, TODO)
│   └── 05_run_end_to_end.py                 # Phase 006 placeholder (NEW, TODO)
├── src/
│   └── cdf_agent_monitoring/
│       ├── __init__.py                      # Package init (NEW)
│       ├── config.py                        # Project constants (NEW)
│       ├── cdf_reader.py                    # Phase 002 placeholder (NEW, TODO)
│       ├── event_builder.py                 # Phase 002 placeholder (NEW, TODO)
│       ├── rule_based_agent.py              # Phase 004 placeholder (NEW, TODO)
│       ├── alert_writer.py                  # Phase 005 placeholder (NEW, TODO)
│       ├── notification_builder.py          # Phase 005 placeholder (NEW, TODO)
│       └── run_logger.py                    # Execution logging (NEW)
└── tests/
    ├── test_config.py                       # test_event_builder.py unit tests (NEW, minimal)
    └── test_run_logger.py                   # test_rule_based_agent.py unit tests (NEW, minimal)
```

**Structure Decision**: Single-project Python package structure appropriate for Databricks notebooks + supporting SQL scripts. Project is data-driven (no web services, no APIs exposed); monitoring tables are internal to Databricks workspace. Placeholder modules for future phases allow incremental implementation and dependency planning.

## Phase 0: Research

**Objective**: Resolve any technical unknowns or dependencies that block implementation.

### Research Tasks & Findings

#### Task 1: Databricks Delta Table Creation in Serverless Environment

**Finding**: Delta table creation in Databricks serverless is straightforward using standard SQL (`CREATE TABLE ... USING DELTA`). No special configuration required; serverless compute handles DDL without additional permissions beyond catalog access.

**Rationale**: Databricks serverless is fully compatible with Delta DDL. No Spark cluster tuning or custom configurations needed.

#### Task 2: Primary Key and Unique Constraint Support in Databricks Delta

**Finding**: Databricks Delta supports:
- PRIMARY KEY (informational, not enforced at write time; used for query optimization and constraint awareness)
- UNIQUE constraints (informational; used for deduplication awareness)
- NOT NULL constraints (enforced at write time)

**Rationale**: For Phase 000, PRIMARY KEY and UNIQUE constraints are documented in schema but not enforced by Delta directly. Enforcement is delegated to application logic in later phases (Phase 002-005) using NOT EXISTS or MERGE logic. This is the standard Databricks pattern.

#### Task 3: Idempotent SQL Pattern for Multi-Table Schema Creation

**Finding**: Use `CREATE TABLE IF NOT EXISTS` for all table creation; use `CREATE SCHEMA IF NOT EXISTS` for schema creation. Pair with explicit schema definitions to ensure re-running scripts doesn't fail or overwrite existing tables.

**Rationale**: Standard pattern in Databricks; safe for re-execution and aligns with Principle IV (Data Safety & Idempotency).

#### Task 4: Human-Readable Logging in Databricks Notebooks

**Finding**: Use `print()` and `dbutils.notebook.run()` callbacks for progress logging. For Phase 000, simple print with checkmarks (✓) and status messages sufficient; structured logging deferred to later phases.

**Rationale**: Phase 000 is interactive notebook; human-readable output provides immediate feedback. Structured logging (JSON) added in later phases when log storage is required.

#### Task 5: Databricks Git Folder Integration for Local Sync

**Finding**: Databricks workspace supports Git folder integration. Push local files to a Git branch, pull into Databricks Git folder, then execute notebooks directly from the Databricks UI or REST API. No special authentication required beyond workspace access.

**Rationale**: Enables local development (CLI, IDE) + Databricks execution workflow. Allows version control and team collaboration.

**Phase 0 Output**: All technical unknowns resolved. Ready for Phase 1 design.

## Phase 1: Design & Contracts

**Prerequisites**: Phase 0 research complete (✓ above)

### Data Model

**Entities**: 

1. **Source Table: sales_info** (existing, not modified in Phase 000)
   - PK: sls_ord_num (business key for this use case)
   - Columns: 18 total (see spec, Key Entities section)
   - Format: Delta (validated in Phase 000)
   - CDF: Enabled in Phase 001 (not enabled in Phase 000)

2. **Monitoring Schema** (created in Phase 000)
   - 5 tables: agent_rules, change_events, agent_alerts, notification_log, agent_run_log
   - All managed Delta tables
   - Explicit PKs, NOT NULL constraints, composite UKs (see data-model.md below)

### File: data-model.md

**[See generated file below]**

### Contracts

**No external contracts** for Phase 000 — the project is internal to Databricks (monitoring tables, notebooks). Contracts will be added in later phases when:
- Phase 007 interfaces with Genie (external LLM integration)
- Phase 008 interfaces with external notification systems (email, Teams, Slack)

For Phase 000, there are no public APIs, CLI contracts, or external system boundaries.

**Deliverable**: contracts/ directory is empty (no contracts for Phase 000).

### File: quickstart.md

**[See generated file below]**

### Agent Context Update

The agent context in CLAUDE.md will be updated to reference the implementation plan (this file) for future development phases. The update is deferred until all planning phases complete and the plan file is finalized.

**Placeholder for agent context reference**:
```
# SPECKIT START
Plan: specs/000-project-bootstrap/plan.md
# SPECKIT END
```

---

## Generated Artifacts

### data-model.md

```markdown
# Data Model: Project Bootstrap (Phase 000)

## Overview

Phase 000 establishes two data domains:
1. **Source Table** (read-only, existing): sales_info in bronz schema
2. **Monitoring Schema** (read-write, created): Five managed Delta tables for CDF events, alerts, notifications, and audit logging

## Source Table: sales_info

**Full Name**: databricks_arrow_cata.bronz.sales_info

**Format**: Delta (validated in Phase 000, CDF enablement deferred to Phase 001)

**Ownership**: External data team (not modified by monitoring project)

**Columns** (18 total):

| Column | Type | Notes |
|--------|------|-------|
| sls_ord_num | STRING | **Business Key** — Unique sales order identifier |
| sls_prd_key | STRING | Product key (context column for alerts) |
| sls_cust_id | STRING | Customer ID (context column) |
| sls_order_dt | TIMESTAMP | Order date |
| sls_ship_dt | TIMESTAMP | Ship date |
| sls_due_dt | TIMESTAMP | Due date |
| sls_sales | DECIMAL | Sales amount (context column, also watched in future rules) |
| sls_quantity | LONG | Quantity ordered (context column) |
| sls_price | DECIMAL | **Watched Column for Phase 000** — Price per unit |
| _rescued_data | STRING | Databricks rescue column (schema drift handling) |
| _source_file_path | STRING | Ingestion metadata |
| _source_file_name | STRING | Ingestion metadata |
| _source_file_size | LONG | Ingestion metadata |
| _source_file_modification_time | TIMESTAMP | Ingestion metadata |
| _ingest_ts | TIMESTAMP | Ingestion timestamp |
| _source_system | STRING | Source system name |
| _source_schema | STRING | Source schema name |
| _source_table | STRING | Source table name |

**Constraints**:
- PK: sls_ord_num (implied; used as deduplication key with watched_column + commit_version in later phases)
- Index: CDF will add internal tracking (Phase 001)

**Lifecycle**: Append-only (new rows added, existing rows updated in-place via CDF)

---

## Monitoring Schema: databricks_arrow_cata.monitoring

**Purpose**: Centralized monitoring table schema for CDF detection, rule-based alerting, and notification logging

**Ownership**: Monitoring project (created and maintained by Phase 000+)

### Table 1: agent_rules

**Purpose**: Store rule definitions for monitoring events

**Columns**:

| Column | Type | Null | PK/UK | Notes |
|--------|------|------|-------|-------|
| rule_id | STRING | N | PK | e.g., "SALES_PRICE_CHANGE_001" |
| rule_name | STRING | N | | Human-readable rule name |
| catalog_name | STRING | N | | Monitored table's catalog |
| schema_name | STRING | N | | Monitored table's schema |
| table_name | STRING | N | | Monitored table's name |
| business_key_columns | STRING | N | | Comma-separated list of business key columns |
| context_columns | STRING | N | | Comma-separated context columns for alerts |
| watched_column | STRING | N | | The column being monitored for changes |
| condition_type | STRING | N | | Type of condition (e.g., "percent_change") |
| medium_threshold_percent | DECIMAL | N | | MEDIUM alert threshold (e.g., 5.0) |
| high_threshold_percent | DECIMAL | N | | HIGH alert threshold (e.g., 10.0) |
| notification_target_type | STRING | N | | Target type (e.g., "alert_table") |
| notification_target_value | STRING | N | | Target value (e.g., table name) |
| is_active | BOOLEAN | N | | Rule is active (true/false) |
| created_at | TIMESTAMP | N | | Rule creation timestamp |
| updated_at | TIMESTAMP | N | | Last update timestamp |

**Constraints**:
- PK: rule_id

**Lifecycle**: Row per rule definition; updated when rule parameters change

---

### Table 2: change_events

**Purpose**: Store structured events from CDF change detection (populated in Phase 002)

**Columns**:

| Column | Type | Null | PK/UK | Notes |
|--------|------|------|-------|-------|
| event_id | STRING | N | PK | Unique event identifier (UUID or generated) |
| rule_id | STRING | N | FK | Foreign key to agent_rules |
| event_type | STRING | N | | Event type (e.g., "SALES_PRICE_CHANGE") |
| source_table | STRING | N | | Full table name where change occurred |
| business_key_json | STRING | N | UK* | JSON object with business key(s) |
| old_value | STRING | Y | | Previous column value |
| new_value | STRING | Y | | New column value |
| change_percent | DECIMAL | Y | | Percentage change (if numeric) |
| context_json | STRING | Y | | JSON object with context columns |
| watched_column | STRING | N | UK* | Column being monitored for changes |
| commit_version | LONG | N | UK* | Delta table version where change occurred |
| commit_timestamp | TIMESTAMP | N | | Commit timestamp |
| created_at | TIMESTAMP | N | | Event creation timestamp |

**Constraints**:
- PK: event_id
- UK: (rule_id, business_key_json, watched_column, commit_version) — prevents duplicate event detection [enforced in Phase 002+ via application logic]

**Lifecycle**: Append-only; one row per detected change; deduplicated by (rule_id, business_key, watched_column, commit_version)

---

### Table 3: agent_alerts

**Purpose**: Store rule-based agent decisions and alert metadata

**Columns**:

| Column | Type | Null | PK/UK | Notes |
|--------|------|------|-------|-------|
| alert_id | STRING | N | PK | Unique alert identifier |
| event_id | STRING | N | FK | Foreign key to change_events |
| rule_id | STRING | N | FK | Foreign key to agent_rules |
| severity | STRING | N | | Alert severity: "HIGH", "MEDIUM", or "LOW" |
| should_notify | BOOLEAN | N | | Whether notification should be sent |
| reason | STRING | N | | Human-readable reason for severity |
| recommended_action | STRING | Y | | Suggested action (e.g., "Review sales price change") |
| agent_type | STRING | N | | Agent type that created alert (e.g., "RULE_BASED_AGENT") |
| alert_status | STRING | N | | Status: "CREATED", "NOTIFICATION_LOGGED", "ENRICHED" |
| genie_context_json | STRING | Y | | Genie enrichment (Phase 007) |
| created_at | TIMESTAMP | N | | Alert creation timestamp |
| updated_at | TIMESTAMP | N | | Last update timestamp |

**Constraints**:
- PK: alert_id
- UK: (event_id, rule_id) — one alert per event per rule [enforced in Phase 004+ via application logic]

**Lifecycle**: Append-mostly; one row per event-rule pair; status updated when enriched or notified

---

### Table 4: notification_log

**Purpose**: Store notification records (audit-table-only in Phase 000-006, external delivery in Phase 008)

**Columns**:

| Column | Type | Null | PK/UK | Notes |
|--------|------|------|-------|-------|
| notification_id | STRING | N | PK | Unique notification identifier |
| alert_id | STRING | N | FK | Foreign key to agent_alerts |
| rule_id | STRING | N | FK | Foreign key to agent_rules |
| notification_type | STRING | N | | Type: "ALERT_TABLE_ONLY" (Phase 000-006), "EMAIL", "TEAMS", "SLACK" (Phase 008) |
| subject | STRING | Y | | Notification subject |
| body | STRING | N | | Notification message body |
| delivery_status | STRING | N | | Status: "LOGGED", "SENT", "FAILED" |
| created_at | TIMESTAMP | N | | Notification creation timestamp |
| sent_at | TIMESTAMP | Y | | Delivery timestamp (if external delivery) |

**Constraints**:
- PK: notification_id

**Lifecycle**: Append-only; one row per notification event; delivery_status updated on send attempt

---

### Table 5: agent_run_log

**Purpose**: Log workflow execution traces and status for audit and debugging

**Columns**:

| Column | Type | Null | PK/UK | Notes |
|--------|------|------|-------|-------|
| run_id | STRING | N | PK | Unique run identifier (UUID) |
| phase | STRING | N | | Phase number (e.g., "000", "001", "002") |
| status | STRING | N | | Status: "STARTED", "IN_PROGRESS", "COMPLETED", "FAILED" |
| message | STRING | Y | | Error or summary message |
| row_count | LONG | Y | | Rows processed/created |
| created_at | TIMESTAMP | N | | Run start timestamp |
| completed_at | TIMESTAMP | Y | | Run end timestamp |

**Constraints**:
- PK: run_id

**Lifecycle**: One row per phase execution; status and completed_at updated on completion

---

## Relationships

```
agent_rules (1) ──→ (M) change_events
           └──→ (M) agent_alerts
           └──→ (M) notification_log
           └──→ (M) agent_run_log

change_events (1) ──→ (M) agent_alerts

agent_alerts (1) ──→ (M) notification_log

sales_info (source table) ── referenced by ── change_events (source_table column)
```

---

## State Transitions

### agent_alerts status lifecycle (Phase 000+):
```
CREATED → NOTIFICATION_LOGGED → ENRICHED (Phase 007, optional)
           ↓
        [end state for Phase 000-006]
```

### notification_log delivery_status lifecycle (Phase 000+):
```
Phase 000-006: LOGGED (only)
Phase 008+:    LOGGED → SENT or FAILED
```

---

## Phase 000 Scope (Data Model)

Phase 000 **creates** the schema and all 5 monitoring tables with proper structure, constraints, and documented columns. Phase 000 does **not**:
- Insert any data into monitoring tables
- Modify source table (sales_info)
- Enable CDF on source table (Phase 001)
- Detect changes (Phase 002)
- Create alerts (Phase 004+)
- Send notifications (Phase 005+)

Data population begins in Phase 002 (CDF detection) and continues through Phase 006 (end-to-end workflow).
```

---

### quickstart.md

```markdown
# Quickstart: Project Bootstrap (Phase 000)

## Overview

This guide validates that Phase 000 bootstrap is working correctly by running the bootstrap notebook and confirming monitoring schema/tables are created.

## Prerequisites

1. **Databricks workspace** with Free Edition or higher
2. **Serverless compute** enabled in workspace
3. **Access to catalog** `databricks_arrow_cata` (must have create/write permissions)
4. **Source table** `databricks_arrow_cata.bronz.sales_info` exists and is populated
5. **Git integration** (optional but recommended): Databricks workspace with Git folder support

## Setup

### Option A: Git Sync (Recommended)

1. **Push local files to Git**:
   ```bash
   git add .
   git commit -m "phase-000: bootstrap project structure"
   git push origin feature/000-project-bootstrap
   ```

2. **Sync into Databricks**:
   - Navigate to **Workspace** → **Git Folders** in Databricks UI
   - Create a new Git folder pointing to the feature branch
   - Or pull the branch into an existing Git folder

3. **Navigate to notebook**:
   - Go to Databricks workspace
   - Find `notebooks/00_project_bootstrap.py` in the synced Git folder
   - Open it in Databricks notebook editor

### Option B: Manual Upload (If Git not available)

1. **Upload notebook**:
   - Download `notebooks/00_project_bootstrap.py` locally
   - In Databricks UI: **Workspace** → **Create** → **Notebook** → **Import** → Select the .py file

2. **Upload SQL scripts** (optional, for reference):
   - Upload `sql/*.sql` files to Databricks workspace or keep locally

## Running Phase 000 Bootstrap

### Step 1: Open the notebook

Navigate to `notebooks/00_project_bootstrap.py` in Databricks workspace.

### Step 2: Configure serverless compute

1. At the top of the notebook, click **Select compute**
2. Choose a **serverless** compute resource (not classic cluster)
3. Click **Attach**

### Step 3: Run all cells

1. Click **Run All** (or run cells sequentially)
2. Watch the output for progress messages:
   ```
   ✓ Validating preconditions...
   ✓ Source table exists and is accessible
   ✓ Checking CDF status...
   ✓ Source table format: delta
   ✓ CDF currently disabled (will enable in Phase 001)
   ✓ Creating monitoring schema...
   ✓ Schema created: databricks_arrow_cata.monitoring
   ✓ Creating agent_rules table...
   ✓ Creating change_events table...
   ✓ Creating agent_alerts table...
   ✓ Creating notification_log table...
   ✓ Creating agent_run_log table...
   ✓ All monitoring tables created successfully
   ✓ Bootstrap complete
   ```

3. **If an error occurs**:
   - Check the error message for the specific issue (e.g., "Source table not found", "Insufficient permissions")
   - Resolve the precondition and re-run the notebook
   - Notebook is idempotent; re-running is safe

### Step 4: Validate results

#### Check 1: Monitoring Schema Exists

Run this query in a Databricks SQL cell:
```sql
SHOW SCHEMAS IN databricks_arrow_cata;
```

**Expected output**: `monitoring` schema listed.

#### Check 2: Monitoring Tables Exist

```sql
SHOW TABLES IN databricks_arrow_cata.monitoring;
```

**Expected output**: 5 tables listed:
- `agent_rules`
- `change_events`
- `agent_alerts`
- `notification_log`
- `agent_run_log`

#### Check 3: Table Schemas

```sql
DESCRIBE TABLE databricks_arrow_cata.monitoring.agent_rules;
```

**Expected output**: All columns listed with proper types (STRING, DECIMAL, TIMESTAMP, BOOLEAN).

Verify:
- `rule_id` is present (PRIMARY KEY)
- `created_at`, `updated_at` are TIMESTAMP

Repeat for other 4 tables.

#### Check 4: Source Table Discovery

The bootstrap notebook should display:

```
SOURCE TABLE DISCOVERY:
========================

Schema: DESCRIBE DETAIL
Table Format: delta
CDF Enabled: false (current)
Row Count: [number]

Sample Rows (first 10):
sls_ord_num | sls_price | sls_prd_key | sls_cust_id
SO12345     | 1000.00   | PK-001      | C12345
[... more rows ...]
```

If CDF is already enabled, that's OK (Phase 001 will skip re-enabling).

#### Check 5: No External Notifications

The bootstrap notebook should **not**:
- Send emails
- Connect to Teams/Slack APIs
- Make external HTTP calls
- Use LangChain or OpenAI APIs

Confirm by reviewing the notebook code — no external API calls present.

#### Check 6: Run Idempotency

Re-run the bootstrap notebook a second time:
```
✓ Monitoring schema already exists (skipped creation)
✓ agent_rules table already exists (skipped creation)
✓ change_events table already exists (skipped creation)
✓ agent_alerts table already exists (skipped creation)
✓ notification_log table already exists (skipped creation)
✓ agent_run_log table already exists (skipped creation)
✓ Bootstrap complete
```

**Expected**: No errors; all "create" operations show "already exists (skipped)".

## What's Next?

- **Phase 001**: Enable Delta Change Data Feed on source table
- **Phase 002**: Implement CDF change detection and event creation
- **Phase 003+**: Add rule definitions, rule-based agent, alerting

## Troubleshooting

### Error: "Source table databricks_arrow_cata.bronz.sales_info not found"

**Cause**: Source table doesn't exist or is not accessible.

**Fix**:
1. Verify the table exists: `SELECT COUNT(*) FROM databricks_arrow_cata.bronz.sales_info;`
2. If missing, work with data team to ensure table is created and populated
3. Ensure your Databricks user has read permissions on the table

### Error: "Permission denied: cannot create schema in catalog"

**Cause**: Insufficient permissions on catalog.

**Fix**:
1. Contact workspace admin to grant `CREATE` and `WRITE` permissions on `databricks_arrow_cata`
2. Alternatively, use a different catalog where you have write permissions (update PLAN.md constants)

### Error: "Serverless compute not available"

**Cause**: Workspace doesn't have serverless enabled or quota exhausted.

**Fix**:
1. Contact workspace admin to enable serverless compute
2. Or temporarily use a small all-purpose cluster (single-node, no workers) for testing

### Notebook runs but monitoring tables don't appear

**Cause**: May be a transient issue or notebook didn't complete.

**Fix**:
1. Check the notebook output for errors (scroll to bottom)
2. Wait 30 seconds for Databricks metadata sync
3. Run validation queries (Check 1-2 above)
4. If still missing, re-run the notebook

## Success Criteria

✅ **Phase 000 is complete when:**

1. Monitoring schema `databricks_arrow_cata.monitoring` exists
2. All 5 monitoring tables exist (agent_rules, change_events, etc.)
3. Each table has correct columns and data types
4. Bootstrap notebook runs without errors
5. CDF status is documented (currently disabled or enabled — no modification)
6. Re-running bootstrap produces idempotent result (no errors, no duplicates)
7. Source table discovery displays schema, detail, and sample rows
8. No external notifications or LLM calls present in code

Proceed to Phase 001 once all criteria met.
```

---

## Summary of Phase 1 Outputs

- ✅ **data-model.md**: Detailed schema for source table and 5 monitoring tables, with relationships and lifecycle
- ✅ **quickstart.md**: Step-by-step validation guide with prerequisites, setup, running, validation checks, and troubleshooting
- ✅ **contracts/**: (Empty for Phase 000 — no external contracts; added in Phases 007-008)

---

## Complexity Tracking

No constitution violations identified. No complexity tracking table needed.

---

## Gate: Constitution Re-Check (Post-Phase 1)

**Re-check after Phase 1 design**:

✅ All 5 principles still satisfied (see Constitution Check above). No violations introduced by design. Design enforces:
- Free Edition / serverless only
- Delta format with PK/UK constraints (idempotency)
- No external APIs or LLM
- Audit logging via agent_run_log
- Data safety via NOT NULL, composite UKs, deduplication strategy

**Gate Result**: ✅ **PASS** — Ready for Phase 2 (task generation).
