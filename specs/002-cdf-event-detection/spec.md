# Feature Specification: CDF Event Detection (Phase 002)

**Feature Branch**: `002-cdf-event-detection`

**Created**: 2026-06-23

**Status**: Draft

**Input**: Phase 002 requirements from PLAN.md and project constitution

## Overview

Phase 001 enabled and validated Delta Change Data Feed (CDF) on the source sales table. Phase 002 consumes that change feed: it reads CDF rows from `databricks_arrow_cata.bronz.sales_info`, detects changes to the watched column `sls_price`, converts each detected change into a structured event row, and persists those events into `databricks_arrow_cata.monitoring.change_events` without creating duplicates on re-run.

This phase stops at producing **change events**. It does not classify severity, does not apply the rule-based agent, and does not create alerts or notifications — those belong to later phases.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect Price Changes from the Change Data Feed (Priority: P1)

As a **data engineer**, I want to **read CDF rows from the source sales table and detect when `sls_price` changed for an order** so that **each meaningful price change is identified as a discrete business event ready for downstream classification**.

**Why this priority**: P1 — Detecting changes from the feed is the core purpose of this phase. Without reliable detection, no events exist for any later phase to act on.

**Independent Test**: Can be fully tested by reading `table_changes()` for the source table, filtering to `update_preimage`/`update_postimage` rows, pairing the old and new image of each updated order, and confirming that an order whose `sls_price` differs between the two images is reported as a detected change while an order whose `sls_price` is unchanged is not.

**Acceptance Scenarios**:

1. **Given** CDF is enabled on the source table, **When** I read the change feed from a starting version, **Then** the workflow returns raw CDF rows including the `_change_type`, `_commit_version`, and `_commit_timestamp` metadata.

2. **Given** raw CDF rows are returned, **When** I filter the feed, **Then** only `update_preimage` and `update_postimage` rows remain (insert, delete, and `update`-without-image change types are excluded).

3. **Given** filtered pre-image and post-image rows, **When** I pair them, **Then** each pair is matched by the same `sls_ord_num` and the same `_commit_version`, producing one old/new pair per updated order per commit.

4. **Given** a matched old/new pair, **When** I compare the old `sls_price` to the new `sls_price`, **Then** the pair is reported as a detected change only if the two prices differ.

5. **Given** a matched pair where `sls_price` is identical in both images (only other columns changed), **When** I compare prices, **Then** the pair is **not** reported as a price-change event.

---

### User Story 2 - Build Structured Event Rows (Priority: P1)

As a **data engineer**, I want to **convert each detected price change into a structured event row that matches the `change_events` table schema** so that **events are consistent, self-describing, and ready to persist and query**.

**Why this priority**: P1 — A detected change has no value until it is shaped into the canonical event structure that every downstream phase consumes. This is the contract between detection and the rest of the workflow.

**Independent Test**: Can be fully tested by feeding one known old/new pair into the event-building logic and confirming the produced row contains every required field, correctly computed `change_percent`, and well-formed `business_key_json` and `context_json`.

**Acceptance Scenarios**:

1. **Given** a detected price change, **When** I build the event row, **Then** it contains all required fields of the `change_events` schema: `event_id`, `rule_id`, `event_type`, `source_table`, `business_key_json`, `old_value`, `new_value`, `change_percent`, `context_json`, `watched_column`, `commit_version`, `commit_timestamp`, and `created_at`.

2. **Given** a detected price change, **When** I build the business key, **Then** `business_key_json` is a JSON object derived from `sls_ord_num` (e.g., `{"sls_ord_num": "SO43697"}`).

3. **Given** a detected price change, **When** I build the context, **Then** `context_json` is a JSON object containing `sls_prd_key`, `sls_cust_id`, `sls_quantity`, and `sls_sales` from the post-image row.

4. **Given** old and new prices, **When** I compute `change_percent`, **Then** it equals `((new - old) / old) * 100`, rounded to a consistent precision, and carries the correct sign (negative for a decrease).

5. **Given** the configured event metadata, **When** I build the event, **Then** `rule_id` is `SALES_PRICE_CHANGE_001`, `event_type` is `SALES_PRICE_CHANGE`, `watched_column` is `sls_price`, and `source_table` is the fully-qualified source table name.

6. **Given** an old price of zero (or null), **When** I compute `change_percent`, **Then** the workflow avoids a divide-by-zero failure and handles the case in a defined, documented way rather than crashing.

---

### User Story 3 - Persist Events Without Duplicates (Priority: P1)

As a **data engineer**, I want to **write detected events into `change_events` using an idempotent merge** so that **re-running the detection on the same change feed never creates duplicate event rows**.

**Why this priority**: P1 — Idempotency is a constitutional requirement (Principle IV). Audit tables are effectively append-only for reporting; duplicate events would corrupt every downstream count and alert.

**Independent Test**: Can be fully tested by running the detection twice against the same change feed and confirming the row count in `change_events` is identical after both runs, and that no two rows share the same deduplication key.

**Acceptance Scenarios**:

1. **Given** newly built event rows, **When** I merge them into `change_events`, **Then** rows that do not already exist are inserted.

2. **Given** the same detection is run a second time over the same feed, **When** the merge runs again, **Then** no new rows are added and the table row count is unchanged.

3. **Given** the deduplication logic, **When** two events would describe the same change, **Then** they are treated as identical based on the combination of `rule_id`, business key (`sls_ord_num`), `watched_column`, and `commit_version`.

4. **Given** a feed containing both an already-persisted change and a brand-new change, **When** the merge runs, **Then** only the brand-new change is inserted and the existing one is left untouched.

---

### User Story 4 - Clear Validation Output and Status (Priority: P2)

As a **data engineer**, I want the detection notebook to **display the intermediate and final data and print a clear status** so that **I can visually confirm the workflow behaved correctly and is safe to re-run**.

**Why this priority**: P2 — Observability is required (Principle V), but the notebook's display behavior is supporting evidence around the core detection/persistence logic rather than the deliverable itself.

**Independent Test**: Can be fully tested by running the notebook and confirming it shows the raw CDF rows, the paired rows, the built event rows, and the final `change_events` contents, then prints either a success message or a clear "no new events" message.

**Acceptance Scenarios**:

1. **Given** the notebook runs, **When** detection completes, **Then** it displays, in order, the raw CDF rows, the paired old/new rows, the built event rows, and the resulting `change_events` output.

2. **Given** at least one new event was detected and persisted, **When** the notebook finishes, **Then** it prints a clear SUCCESS message indicating how many events were written.

3. **Given** no `sls_price` changes are present in the feed (or all detected changes already exist), **When** the notebook finishes, **Then** it prints a clear "no new events" message rather than an error or a misleading success.

4. **Given** CDF is not enabled on the source table, **When** the notebook starts, **Then** it reports that precondition failure clearly and does not attempt to read the change feed.

---

### Edge Cases

- **No update rows in the feed**: If the change feed contains only inserts/deletes (or is empty), no pairs are formed, no events are built, and the notebook prints the "no new events" message.
- **Unchanged watched column**: An update that modifies context columns but leaves `sls_price` identical must not produce an event.
- **Multiple changes to the same order across commits**: Each distinct `_commit_version` for the same order produces its own event; they are not collapsed, because each is a separate change with its own commit metadata.
- **Old price of zero or null**: `change_percent` computation must not divide by zero; the case is handled in a defined way (see Assumptions).
- **Re-running the notebook**: Detection over the same feed must be idempotent — the second run inserts zero new rows.
- **Unpaired image rows**: If a pre-image has no matching post-image (or vice versa) for the same order and commit, the unmatched row is skipped rather than producing a malformed event.
- **CDF not enabled / source missing**: The notebook fails fast with a clear message and does not partially write events.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow MUST verify that Change Data Feed is enabled on `databricks_arrow_cata.bronz.sales_info` before attempting to read the change feed, and report a clear failure if it is not.
- **FR-002**: The workflow MUST read change rows from the source table's Change Data Feed using `table_changes()`.
- **FR-003**: The workflow MUST filter the change feed to retain only `update_preimage` and `update_postimage` rows.
- **FR-004**: The workflow MUST pair each pre-image row with its corresponding post-image row by matching `sls_ord_num` and `_commit_version`.
- **FR-005**: The workflow MUST compare the old and new `sls_price` for each pair and treat the pair as a detected change only when the values differ.
- **FR-006**: The workflow MUST compute `change_percent` as the signed percentage change from old to new `sls_price`.
- **FR-007**: The workflow MUST handle a zero or null old price without failing, in a defined and documented manner.
- **FR-008**: The workflow MUST build `business_key_json` as a JSON object from `sls_ord_num`.
- **FR-009**: The workflow MUST build `context_json` as a JSON object from `sls_prd_key`, `sls_cust_id`, `sls_quantity`, and `sls_sales`.
- **FR-010**: The workflow MUST produce event rows whose fields and types match the `change_events` table schema exactly, populating `rule_id = SALES_PRICE_CHANGE_001`, `event_type = SALES_PRICE_CHANGE`, `watched_column = sls_price`, and the fully-qualified `source_table`.
- **FR-011**: The workflow MUST assign each event a unique `event_id` and a `created_at` timestamp, and MUST carry the source change's `commit_version` and `commit_timestamp`.
- **FR-012**: The workflow MUST persist detected events into `databricks_arrow_cata.monitoring.change_events` using a merge that inserts only events not already present.
- **FR-013**: The workflow MUST prevent duplicate events using the combination of `rule_id`, business key (`sls_ord_num`), `watched_column`, and `commit_version` as the deduplication key, such that re-running over the same feed inserts zero new rows.
- **FR-014**: The notebook MUST display the raw CDF rows, the paired old/new rows, the built event rows, and the final `change_events` contents.
- **FR-015**: The notebook MUST print a clear SUCCESS message (including the count of new events) when events are written, and a clear "no new events" message when none are.
- **FR-016**: The workflow MUST NOT enable CDF, MUST NOT modify the source table, MUST NOT run a test UPDATE, MUST NOT classify severity, and MUST NOT create alerts or notification-log rows.
- **FR-017**: Detection and persistence MUST run on Databricks serverless compute only, with no external network calls, no hardcoded secrets, and no LLM/LangChain/OpenAI/RAG/Genie dependencies.
- **FR-018**: Phase 002 MUST be validated against the live Databricks workspace (via the configured Databricks MCP server or the DEFAULT `.databrickscfg` profile); it MUST NOT be marked successful from local code generation alone.

### Key Entities *(include if feature involves data)*

- **CDF Change Row**: A row returned by `table_changes()` for the source table, carrying the source columns plus `_change_type`, `_commit_version`, and `_commit_timestamp`. Relevant change types here are `update_preimage` (old image) and `update_postimage` (new image).
- **Paired Change**: A logical pairing of one pre-image and one post-image row sharing the same `sls_ord_num` and `_commit_version`, representing one order's update within one commit. Holds old and new `sls_price` plus the post-image context columns.
- **Change Event**: A structured record matching the `change_events` schema: identity (`event_id`), classification metadata (`rule_id`, `event_type`, `watched_column`, `source_table`), the business key (`business_key_json`), the change values (`old_value`, `new_value`, `change_percent`), context (`context_json`), and provenance (`commit_version`, `commit_timestamp`, `created_at`). Deduplicated by (`rule_id`, business key, `watched_column`, `commit_version`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running detection against a change feed that contains at least one `sls_price` update results in exactly one change event per distinct (order, commit) price change appearing in `change_events`.
- **SC-002**: For every detected event, `change_percent` equals the signed percentage change between the old and new price within the documented rounding precision.
- **SC-003**: Every persisted event row conforms to the `change_events` schema with no null values in any NOT NULL column and valid JSON in `business_key_json` and `context_json`.
- **SC-004**: Re-running detection over the same change feed adds zero new rows to `change_events` (100% idempotent), verified by an unchanged row count and no duplicate deduplication keys.
- **SC-005**: An update that does not change `sls_price` produces zero events.
- **SC-006**: The notebook always terminates with an unambiguous status — either a SUCCESS message with the new-event count or a "no new events" message — for both the events-present and no-events cases.
- **SC-007**: Phase 002 success is demonstrated against the live Databricks workspace, with the final `change_events` contents shown as evidence.

## Assumptions

- **CDF availability**: CDF is already enabled on the source table from Phase 001; this phase only validates that fact and reads the feed.
- **Change-feed starting point**: Detection reads the feed from an agreed starting version (e.g., the earliest available CDF version, or a configured baseline). The exact starting-version strategy is an implementation detail to be settled in planning; idempotency via the merge guarantees correctness regardless of overlap.
- **Zero/null old price handling**: When the old `sls_price` is zero or null, `change_percent` is recorded as null (the change is still a detected event, but a meaningful percentage cannot be computed). This default may be refined in planning.
- **Value storage as strings**: `old_value` and `new_value` are stored as strings in `change_events` (per the existing schema), consistent with the event example in PLAN.md.
- **One commit, one pair per order**: A given order is assumed to be updated at most once per commit version, so (`sls_ord_num`, `_commit_version`) uniquely identifies a pre/post image pair.
- **Existing schema reused**: The `change_events` table already exists (created in Phase 000); this phase writes to it and does not alter its schema.
- **Shared constants reused**: `rule_id`, business key, context columns, watched column, and table names come from `src/cdf_agent_monitoring/config.py` rather than being re-hardcoded.

## Out of Scope

- Enabling CDF (done in Phase 001).
- Modifying the source table or running any test UPDATE.
- Running the rule-based agent or classifying severity (HIGH/MEDIUM/LOW).
- Creating alerts, notification-log rows, or any notification.
- Using Genie, LangChain, OpenAI, RAG, or any external LLM.
- Sending external notifications (email/Teams/Slack/webhook).

## Dependencies

- **Phase 000** — monitoring schema and `change_events` table exist.
- **Phase 001** — CDF enabled and validated on the source table.
- **Databricks workspace** — reachable via the configured Databricks MCP server or DEFAULT `.databrickscfg` profile, serverless compute available.
