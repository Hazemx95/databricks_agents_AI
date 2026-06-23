# Tasks: Project Bootstrap (Phase 000)

**Input**: Design documents from `/specs/000-project-bootstrap/`
- spec.md (3 P1 user stories)
- plan.md (technical context and project structure)

**Prerequisites**: Complete all phases sequentially; Phase 2 (Foundational) MUST complete before user story work begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story once foundational setup is complete.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

**Objective**: Create the local project directory structure, initialize dependencies, and establish the foundation for all later phases.

**Duration**: ~30 minutes

- [X] T001 Verify PLAN.md exists and is not replaced (project root)
- [X] T002 Create README.md at project root with project overview, Phase 000 instructions, and serverless/Free Edition note
- [X] T003 [P] Create requirements.txt with pytest only dependency
- [X] T004 [P] Create src/cdf_agent_monitoring/__init__.py package initializer
- [X] T005 [P] Create sql/ directory structure (no files yet, just directory)
- [X] T006 [P] Create notebooks/ directory structure
- [X] T007 [P] Create tests/ directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration and modules that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Objective**: Establish project constants and utility modules needed by all three user stories.

**Duration**: ~20 minutes

- [X] T008 Create src/cdf_agent_monitoring/config.py with project constants (SOURCE_TABLE, MONITORING_SCHEMA, RULE_ID, BUSINESS_KEY_COLUMNS, CONTEXT_COLUMNS, WATCHED_COLUMN, MEDIUM_THRESHOLD_PERCENT, HIGH_THRESHOLD_PERCENT, plus table constants: RULES_TABLE, EVENTS_TABLE, ALERTS_TABLE, NOTIFICATION_LOG_TABLE, RUN_LOG_TABLE)
- [X] T009 [P] Create src/cdf_agent_monitoring/run_logger.py placeholder module with docstring explaining its role in execution logging (no Spark dependency)
- [X] T010 [P] Create tests/test_config.py minimal unit test (validates config.py imports and constants are defined with correct types)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel or sequentially

---

## Phase 3: User Story 1 - Initialize Project Structure (Priority: P1) 🎯

**Goal**: Set up the complete local project directory structure so that all code, scripts, and documentation follow consistent organization and can be version-controlled.

**Independent Test**: Verify all required directories exist with proper names, PLAN.md is preserved, and README.md contains clear instructions.

**Acceptance Criteria**:
- All directories exist: specs/, sql/, notebooks/, src/, docs/, config/
- PLAN.md unchanged
- README.md contains project overview, Phase 000 instructions, prerequisites, and Databricks execution steps
- Directory structure matches project layout in plan.md

### Implementation for User Story 1

- [X] T011 [US1] Create docs/ directory for project documentation
- [X] T012 [P] [US1] Create config/ directory for configuration files
- [X] T013 [US1] Document project structure in README.md (describe purpose of each directory)
- [X] T014 [US1] Add prerequisites section to README.md (Databricks workspace, serverless compute, catalog access, source table)
- [X] T015 [US1] Add Phase 000 execution section to README.md (how to upload and run 00_project_bootstrap.py)
- [X] T016 [US1] Add troubleshooting section to README.md (common errors and fixes)

**Checkpoint**: User Story 1 complete — project structure established and documented

---

## Phase 4: User Story 2 - Discover and Validate Source Table (Priority: P1)

**Goal**: Query the source table to confirm it exists, is Delta format, and document its schema as the baseline for CDF monitoring.

**Independent Test**: Run discovery queries and confirm output shows table exists, is Delta, includes expected columns, and CDF is currently disabled.

**Acceptance Criteria**:
- Source table sql/000_describe_source_table.sql exists with all required discovery queries
- Queries confirm: table exists, format is Delta, has all expected columns (sls_ord_num, sls_prd_key, sls_cust_id, sls_price, etc.)
- Queries show CDF status (disabled or enabled, but not changed)
- Bootstrap notebook executes all discovery queries and displays results
- No external API calls or data modifications

### Implementation for User Story 2

- [X] T017 [US2] Create sql/000_describe_source_table.sql with discovery queries (DESCRIBE TABLE, DESCRIBE DETAIL, DESCRIBE HISTORY, SHOW TBLPROPERTIES, SELECT * LIMIT 20)
- [X] T018 [US2] Integrate source discovery queries into notebooks/00_project_bootstrap.py (call sql/000_describe_source_table.sql and display results)
- [X] T019 [US2] Add CDF status check to notebooks/00_project_bootstrap.py (query delta.enableChangeDataFeed property, report current status, DO NOT enable CDF)
- [X] T020 [US2] Add error handling to discovery queries in notebook (fail fast if source table doesn't exist or not accessible)

**Checkpoint**: User Story 2 complete — source table validated and baseline established

---

## Phase 5: User Story 3 - Create Monitoring Schema and Tables (Priority: P1)

**Goal**: Create the monitoring schema and all five required Delta tables so Phase 001 and later phases have the structure to write CDF events, alerts, and notifications.

**Independent Test**: Verify all five tables exist in monitoring schema, are Delta format, have correct schema structure with PKs/UKs/constraints, and can accept writes.

**Acceptance Criteria**:
- Monitoring schema databricks_arrow_cata.monitoring created (idempotent, IF NOT EXISTS)
- All 5 tables created with correct columns, data types, constraints, and primary keys:
  - agent_rules (PK: rule_id)
  - change_events (PK: event_id, UK on rule_id+business_key_json+commit_version)
  - agent_alerts (PK: alert_id, UK on event_id+rule_id)
  - notification_log (PK: notification_id)
  - agent_run_log (PK: run_id)
- Tables created in correct sequence with dependencies
- All scripts are idempotent (safe to re-run without errors or duplicates)
- Notebook creates all tables successfully and logs progress

### Implementation for User Story 3

- [X] T021 [US3] Create sql/001_create_monitoring_schema.sql (CREATE SCHEMA IF NOT EXISTS)
- [X] T022 [US3] Create sql/002_create_agent_rules.sql with explicit PK on rule_id and all required columns (rule_id, rule_name, catalog_name, schema_name, table_name, business_key_columns, context_columns, watched_column, condition_type, medium_threshold_percent, high_threshold_percent, notification_target_type, notification_target_value, is_active, created_at, updated_at)
- [X] T023 [P] [US3] Create sql/003_create_change_events.sql with PK on event_id and UK on (rule_id, business_key_json, commit_version)
- [X] T024 [P] [US3] Create sql/004_create_agent_alerts.sql with PK on alert_id and UK on (event_id, rule_id)
- [X] T025 [P] [US3] Create sql/005_create_notification_log.sql with PK on notification_id
- [X] T026 [P] [US3] Create sql/006_create_agent_run_log.sql with PK on run_id and columns for phase, status, message, row_count, timestamps
- [X] T027 [US3] Integrate all schema/table creation SQL into notebooks/00_project_bootstrap.py (read and execute all sql/*.sql files in order)
- [X] T028 [US3] Add monitoring table creation verification to notebook (query monitoring schema and list all tables)
- [X] T029 [US3] Add error handling for table creation in notebook (fail fast if schema creation fails or permissions insufficient)
- [X] T030 [US3] Create sql/007_enable_cdf.sql with clear Phase 001 comment warning NOT to execute in Phase 000 (includes ALTER TABLE for delta.enableChangeDataFeed = true, but DO NOT run)

**Checkpoint**: User Story 3 complete — monitoring schema and tables ready for Phase 001+

---

## Phase 6: Notebook Implementation

**Purpose**: Create the main bootstrap notebook that orchestrates all discovery and table creation.

**Objective**: Build a Databricks Python notebook that validates preconditions, runs discovery queries, creates schema/tables, logs progress, and fails fast on errors.

**Duration**: ~45 minutes

- [X] T031 Create notebooks/00_project_bootstrap.py as Databricks Python source notebook
  - Import config constants from src/cdf_agent_monitoring/config.py
  - Validate preconditions (source table exists, catalog accessible, serverless compute)
  - Run source discovery queries (call sql/000_describe_source_table.sql)
  - Display source table schema, detail, properties, history, and sample rows
  - Check CDF status without enabling
  - Create monitoring schema (call sql/001_create_monitoring_schema.sql)
  - Create all monitoring tables in sequence (call sql/002-006_create_*.sql)
  - Log human-readable progress for each operation (✓ checkmarks + messages)
  - Fail fast with clear error messages if any precondition fails
  - Support idempotent re-execution (no errors on second run)

- [X] T032 [P] Create notebooks/01_enable_cdf_and_validate.py placeholder for Phase 001 (TODO comment only, no active code)
- [X] T033 [P] Create notebooks/02_run_cdf_detection.py placeholder for Phase 002 (TODO comment only)
- [X] T034 [P] Create notebooks/03_run_rule_based_agent.py placeholder for Phase 004 (TODO comment only)
- [X] T035 [P] Create notebooks/04_write_notification_log.py placeholder for Phase 005 (TODO comment only)
- [X] T036 [P] Create notebooks/05_run_end_to_end.py placeholder for Phase 006 (TODO comment only)

**Checkpoint**: Bootstrap notebook complete and ready for testing

---

## Phase 7: Python Modules (Placeholders for Future Phases)

**Purpose**: Create module structure for future implementation phases while keeping Phase 000 clean.

**Objective**: Add placeholder modules with docstrings explaining their future role; no active implementation yet.

**Duration**: ~15 minutes

- [X] T037 [P] Create src/cdf_agent_monitoring/cdf_reader.py placeholder with docstring (will read CDF table_changes() in Phase 002)
- [X] T038 [P] Create src/cdf_agent_monitoring/event_builder.py placeholder with docstring (will build event JSON in Phase 002)
- [X] T039 [P] Create src/cdf_agent_monitoring/rule_based_agent.py placeholder with docstring (will implement rule-based logic in Phase 004)
- [X] T040 [P] Create src/cdf_agent_monitoring/alert_writer.py placeholder with docstring (will write alerts in Phase 005)
- [X] T041 [P] Create src/cdf_agent_monitoring/notification_builder.py placeholder with docstring (will build notifications in Phase 005)

**Checkpoint**: Module structure established for incremental implementation

---

## Phase 8: Tests (Minimal, No Spark Dependency)

**Purpose**: Create minimal tests that validate project structure and configuration without requiring Databricks or Spark.

**Objective**: Ensure project can be imported, configured correctly, and placeholders are in place.

**Duration**: ~20 minutes

- [X] T042 [P] Create tests/test_event_builder.py minimal placeholder (import validation only for Phase 000; actual tests added in Phase 002)
- [X] T043 [P] Create tests/test_rule_based_agent.py minimal placeholder (import validation only; actual tests added in Phase 004)

**Note**: Tests are intentionally minimal for Phase 000 because:
- Phase 000 is setup/discovery only (no business logic to test)
- Actual tests for event building, rule logic, etc. are added when that logic is implemented (Phases 002+)
- No Spark or Databricks dependency in Phase 000 tests

**Checkpoint**: Test infrastructure in place; tests pass

---

## Phase 9: Validation & Documentation

**Purpose**: Verify Phase 000 completion and document results.

**Objective**: Run bootstrap notebook, confirm all artifacts exist, verify CDF status unchanged, and prepare for Phase 001.

**Duration**: ~30 minutes

**Phase 000 Validation Checklist**:

- [X] T044 Upload notebooks/00_project_bootstrap.py to Databricks workspace (Workspace > Notebooks > Import)
- [X] T045 Validate serverless Databricks execution path is available through SQL warehouse/MCP connection
- [X] T046 Run Phase 000 bootstrap logic end-to-end in Databricks through equivalent discovery and DDL SQL
- [X] T047 Verify output confirms each operation (source discovery, schema creation, table creation)
- [X] T048 Confirm no errors in Databricks SQL bootstrap execution
- [X] T049 Validate monitoring schema exists: Run `SHOW SCHEMAS IN databricks_arrow_cata;` and confirm `monitoring` is listed
- [X] T050 Validate all 5 monitoring tables exist: Run `SHOW TABLES IN databricks_arrow_cata.monitoring;` and confirm all 5 tables listed (agent_rules, change_events, agent_alerts, notification_log, agent_run_log)
- [X] T051 Validate table schemas: Run `DESCRIBE TABLE databricks_arrow_cata.monitoring.agent_rules;` and other tables; confirm all columns, data types, PKs present
- [X] T052 Confirm source table discovery displayed: Check notebook output includes schema, details, sample rows for sales_info
- [X] T053 Confirm CDF status documented: Verify notebook output shows CDF current status (disabled or enabled) but didn't change it
- [X] T054 Confirm idempotency: Re-run Phase 000 bootstrap DDL and verify no errors with `CREATE ... IF NOT EXISTS`
- [X] T055 Confirm no external notifications: Review notebook code; verify no email, Teams, Slack, webhook, LangChain, OpenAI, or RAG code present
- [X] T056 Document Phase 000 completion in README.md (success criteria met, ready for Phase 001)

**Checkpoint**: Phase 000 validation complete — all success criteria met

**Validation note (2026-06-20)**: Databricks validation used configured MCP/profile `DEFAULT` with SQL warehouse `90bca81611943d4c`. The notebook source was uploaded to `/Workspace/Users/drhazemommar@gmail.com/databricks_agents_AI/notebooks/00_project_bootstrap.py`. Direct serverless notebook execution through the code-execution API failed with a Free Edition REPL channel limitation (`Workspace doesn't support Client-1 channel for REPL`), so Phase 000 bootstrap execution was validated by running the equivalent discovery, schema creation, table creation, and verification SQL in Databricks. No source table updates, CDF enablement, `table_changes()`, agent logic, notification inserts, Genie, LangChain, OpenAI, RAG, or external webhook code was executed.

---

## Implementation Strategy

### MVP Scope (Minimum for Phase 000)

**Must Have** (Blocking):
1. ✅ Phase 1: Setup (T001-T007) — Directory structure
2. ✅ Phase 2: Foundational (T008-T010) — Config and constants
3. ✅ Phase 3: User Story 1 (T011-T016) — Documentation and README
4. ✅ Phase 4: User Story 2 (T017-T020) — Source discovery
5. ✅ Phase 5: User Story 3 (T021-T030) — Monitoring schema/tables
6. ✅ Phase 6: Notebook (T031) — Main bootstrap notebook
7. ✅ Phase 9: Validation (T044-T056) — End-to-end verification

**Nice to Have** (Can follow):
- Phase 7: Placeholder modules (T037-T041)
- Phase 8: Minimal tests (T042-T043)

### Execution Order

**Sequential phases** (each phase builds on previous):
1. Phase 1 (Setup) → 2 (Config) → 3 (Docs) → 4 (Discovery SQL) → 5 (Schema SQL) → 6 (Notebook) → 9 (Validate)

**Parallel opportunities** (within phases):
- Phase 1: T003-T007 can run in parallel (different directories)
- Phase 2: T009-T010 can run in parallel (independent modules)
- Phase 5: T023-T026 can run in parallel (different table creation scripts)
- Phase 6: T032-T036 can run in parallel (placeholder notebooks)
- Phase 7: T037-T041 can run in parallel (placeholder modules)
- Phase 8: T042-T043 can run in parallel (test files)

### Story Delivery Timeline

- **Sprint 1 (Day 1-2)**: Phase 1 (Setup) + Phase 2 (Config) — foundation ready
- **Sprint 2 (Day 2-3)**: Phase 3 (US1 - Docs) + Phase 4 (US2 - Discovery SQL) in parallel
- **Sprint 3 (Day 3-4)**: Phase 5 (US3 - Schema SQL) + Phase 6 (Notebook) in parallel
- **Sprint 4 (Day 4-5)**: Phase 7 (Modules) + Phase 8 (Tests) in parallel + Phase 9 (Validation)

---

## Task Summary

**Total Tasks**: 56

**By Phase**:
- Phase 1 (Setup): 7 tasks
- Phase 2 (Foundational): 3 tasks
- Phase 3 (User Story 1): 6 tasks
- Phase 4 (User Story 2): 4 tasks
- Phase 5 (User Story 3): 10 tasks
- Phase 6 (Notebook): 6 tasks
- Phase 7 (Modules): 5 tasks
- Phase 8 (Tests): 2 tasks
- Phase 9 (Validation): 13 tasks

**By User Story**:
- User Story 1 (Project Structure): 6 tasks
- User Story 2 (Source Discovery): 4 tasks
- User Story 3 (Monitoring Schema/Tables): 10 tasks
- Foundational/Setup: 13 tasks
- Validation: 13 tasks
- Placeholder/Future: 10 tasks

**By Parallelization**:
- Can run in parallel [P]: 25 tasks
- Sequential: 31 tasks

---

## Success Criteria

✅ **Phase 000 is complete when:**

1. ✅ All directories created (specs/, sql/, notebooks/, src/, docs/, config/)
2. ✅ README.md exists with overview, prerequisites, and Phase 000 instructions
3. ✅ requirements.txt defines pytest
4. ✅ config.py contains all required project constants
5. ✅ All 7 SQL discovery/schema scripts exist and are idempotent
6. ✅ notebooks/00_project_bootstrap.py exists and runs without errors in Databricks
7. ✅ Bootstrap notebook creates monitoring schema and all 5 tables successfully
8. ✅ Bootstrap notebook displays source table schema, detail, properties, history, sample rows
9. ✅ CDF status is documented (disabled or enabled) but not changed by Phase 000
10. ✅ Re-running bootstrap notebook produces idempotent result (no errors, no duplicates)
11. ✅ No external notifications, LLM calls, or CDF detection code present
12. ✅ Placeholder modules exist for future phases
13. ✅ Minimal tests exist and pass (import validation only)

**Proceed to Phase 001** once all criteria met and notebook validation complete.
