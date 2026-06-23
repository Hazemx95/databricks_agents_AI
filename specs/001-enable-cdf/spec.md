# Feature Specification: Enable and Validate Change Data Feed (Phase 001)

**Feature Branch**: `feature/001-enable-cdf`

**Created**: 2026-06-23

**Status**: Draft

**Input**: Phase 001 requirements from PLAN.md and project constitution

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enable Change Data Feed on Source Table (Priority: P1)

As a **data engineer**, I want to **enable Delta Change Data Feed (CDF) on the source sales table** so that **every future row-level change is recorded and can be consumed by the downstream monitoring workflow**.

**Why this priority**: P1 — CDF is the foundational mechanism for the entire monitoring workflow. Without it, no change events can be detected in any later phase. This is the central deliverable of Phase 001.

**Independent Test**: Can be fully tested by running the enable step and then confirming that the `delta.enableChangeDataFeed` table property reads `true`, with no change to the table's data or column structure.

**Acceptance Scenarios**:

1. **Given** the source table `databricks_arrow_cata.bronz.sales_info` exists and is Delta format, **When** I check its current CDF status, **Then** the workflow reports whether `delta.enableChangeDataFeed` is currently enabled or not.

2. **Given** CDF is not yet enabled, **When** I run the enable step, **Then** the table property `delta.enableChangeDataFeed` is set to `true` and the change succeeds without altering existing rows or columns.

3. **Given** CDF is already enabled, **When** I run the enable step again, **Then** the workflow completes without error and leaves the property as `true` (idempotent — no duplicate or destructive action).

4. **Given** the source table does not exist or is not Delta format, **When** I run the precondition check, **Then** the workflow fails fast with a clear, actionable error message and does not attempt to enable CDF.

---

### User Story 2 - Capture Baseline Version Before Test Update (Priority: P1)

As a **data engineer**, I want to **capture the table's current commit version before making any test change** so that **I can read change records precisely from that point forward and reproduce the validation reliably**.

**Why this priority**: P1 — `table_changes()` requires a starting version. Capturing the baseline before the test update is what makes the validation deterministic and repeatable, and it establishes the pattern every later phase reuses.

**Independent Test**: Can be fully tested by recording the current version, confirming it is a non-negative integer, and confirming it is captured strictly before the test update is applied.

**Acceptance Scenarios**:

1. **Given** CDF is enabled, **When** I capture the baseline, **Then** the workflow records the current commit version of the table as a numeric value.

2. **Given** the baseline version is captured, **When** I display it, **Then** the baseline version is shown clearly and is available for use in the validation query.

3. **Given** the baseline is captured before the test update, **When** the test update later commits, **Then** the new commit version is strictly greater than the baseline version.

---

### User Story 3 - Apply Safe Test Update and Validate CDF Records (Priority: P1)

As a **data engineer**, I want to **apply one controlled price update to a single known order and then read the change records** so that **I can prove CDF captures both the old (pre-image) and new (post-image) values of `sls_price`**.

**Why this priority**: P1 — This is the validation that proves CDF works end-to-end for the project's first business event (`SALES_PRICE_CHANGE`). It is the explicit acceptance condition for Phase 001.

**Independent Test**: Can be fully tested by updating `sls_price` for one order, reading `table_changes()` from the baseline version, and confirming both `update_preimage` and `update_postimage` rows appear for that order with the correct old and new prices.

**Acceptance Scenarios**:

1. **Given** the baseline version is captured, **When** I update `sls_price` by 15% for `sls_ord_num = 'SO43697'`, **Then** exactly one order's price row is changed and no other rows are affected.

2. **Given** the update has committed, **When** I read `table_changes()` from the baseline version filtered to `sls_ord_num = 'SO43697'`, **Then** the result includes one `update_preimage` row and one `update_postimage` row for that order.

3. **Given** the change records are returned, **When** I inspect them, **Then** the `update_preimage` row shows the original `sls_price` and the `update_postimage` row shows the new `sls_price` (original × 1.15).

4. **Given** the validation completes, **When** I view the summary, **Then** the workflow displays the old price, the new price, the commit version of the change, and an overall validation status (PASS/FAIL).

5. **Given** the order `SO43697` does not exist in the source table, **When** I run the update, **Then** the workflow reports that no rows matched and surfaces a clear warning rather than silently passing.

---

### Edge Cases

- **CDF already enabled at start**: The enable step must be idempotent and treat an already-`true` property as success, not as an error.
- **Order `SO43697` missing**: If the target order is absent, the update affects zero rows; the workflow must detect and report this rather than declaring a false PASS.
- **Re-running the whole phase**: Each re-run applies a further +15% and creates a new commit. The validation must read from the baseline captured in that same run so the displayed old/new prices and commit version are internally consistent.
- **No change records returned**: If `table_changes()` returns no `update_preimage`/`update_postimage` rows for the order, validation status must be FAIL with a clear message.
- **Baseline captured after the update**: This is an error condition; the baseline must always be captured before the test update, otherwise the change will not appear in the window.
- **Source table not Delta / missing**: Precondition check fails fast before any modification is attempted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow MUST verify the source table `databricks_arrow_cata.bronz.sales_info` exists and is Delta format before any modification, and MUST fail fast with a clear, actionable message if not.
- **FR-002**: The workflow MUST check and report the current CDF status (`delta.enableChangeDataFeed`) of the source table before enabling it.
- **FR-003**: The workflow MUST enable CDF on the source table by setting `delta.enableChangeDataFeed = true`.
- **FR-004**: The enable step MUST be idempotent — running it when CDF is already enabled completes successfully and leaves the property as `true`.
- **FR-005**: The workflow MUST confirm, after the enable step, that the `delta.enableChangeDataFeed` property reads `true`.
- **FR-006**: The workflow MUST capture the source table's current commit version as a baseline **before** applying the test update, and MUST display it.
- **FR-007**: The workflow MUST apply a single test update that increases `sls_price` by 15% for `sls_ord_num = 'SO43697'` only.
- **FR-008**: The test update MUST affect only the targeted order and MUST NOT alter any other rows or any columns other than `sls_price`.
- **FR-009**: The workflow MUST report the number of rows affected by the test update and surface a clear warning if zero rows matched.
- **FR-010**: The workflow MUST read change records using `table_changes()` starting from the captured baseline version, filtered to `sls_ord_num = 'SO43697'`.
- **FR-011**: The workflow MUST validate that the change records contain both an `update_preimage` row and an `update_postimage` row for the targeted order.
- **FR-012**: The workflow MUST extract the old `sls_price` (from the pre-image) and the new `sls_price` (from the post-image) for the targeted order.
- **FR-013**: The workflow MUST display the old price, new price, commit version of the change, and an overall validation status (PASS/FAIL).
- **FR-014**: The workflow MUST set validation status to FAIL with a clear message when the required pre-image/post-image rows are not found.
- **FR-015**: All steps MUST execute in Databricks Free Edition using serverless compute only, with no classic clusters, no hardcoded secrets, and no external API calls.
- **FR-016**: The workflow MUST NOT create change events, alerts, notification logs, Genie context, or any external notification — those are out of scope for this phase.

### Key Entities *(include if feature involves data)*

- **Source Table (`databricks_arrow_cata.bronz.sales_info`)**: The Delta table being monitored. Relevant columns for this phase: `sls_ord_num` (business key), `sls_price` (watched column), plus context columns `sls_prd_key`, `sls_cust_id`, `sls_quantity`, `sls_sales`. The CDF property `delta.enableChangeDataFeed` is toggled on this table.
- **Baseline Version**: A numeric commit version of the source table captured before the test update; the starting point for the `table_changes()` window.
- **Change Records (`table_changes()` output)**: Row-level change records produced by CDF. Each row carries a `_change_type` (e.g., `update_preimage`, `update_postimage`), `_commit_version`, and `_commit_timestamp` alongside the table's data columns. For an UPDATE, a matched pre-image/post-image pair represents the old and new state of the changed row.
- **Validation Result**: The phase outcome — old `sls_price`, new `sls_price`, commit version of the change, and a PASS/FAIL status indicating whether CDF correctly captured the price change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After running the phase, the source table reports `delta.enableChangeDataFeed = true`.
- **SC-002**: A baseline commit version is captured and displayed before the test update is applied.
- **SC-003**: The test update changes the price of exactly one order (`SO43697`) and reports exactly 1 row affected.
- **SC-004**: Reading `table_changes()` from the baseline version returns exactly one `update_preimage` row and one `update_postimage` row for `SO43697`.
- **SC-005**: The displayed new `sls_price` equals the displayed old `sls_price` multiplied by 1.15 (within rounding tolerance).
- **SC-006**: The phase produces a clear, single PASS/FAIL validation status that reads PASS only when both pre-image and post-image rows are present with correct old/new prices.
- **SC-007**: Re-running the enable step does not error and does not change the data or schema of the source table.
- **SC-008**: No rows are written to any monitoring table (`change_events`, `agent_alerts`, `notification_log`) and no external notification is sent during this phase.

## Assumptions

- **Phase 000 is complete**: The source table exists, is confirmed Delta, and the monitoring schema/tables already exist (not used in this phase, but present).
- **Order `SO43697` exists**: The targeted order is present in the source table with a non-null `sls_price`, consistent with the example in PLAN.md.
- **Write permissions available**: The executing user has `ALTER` and `UPDATE` permission on `databricks_arrow_cata.bronz.sales_info`.
- **Serverless compute available**: Execution occurs on Databricks Free Edition serverless compute; standard Databricks SQL and Delta `table_changes()` are supported.
- **Modifying the bronze source table is acceptable**: A controlled +15% price update to one order is an approved, intentional test action for validating CDF (per PLAN.md's recommended test update). This phase intentionally writes to the source table; this is the only phase that does so for validation purposes.
- **CDF captures changes only after enablement**: Change records are available for commits made after CDF is enabled; the baseline is captured at or after enablement so the test update falls inside the window.
- **Standard rounding**: The +15% computation uses the platform's default numeric handling for `sls_price`; small rounding differences are acceptable for the equality check in SC-005.

## Out of Scope

- Building structured change-event JSON or writing to `change_events` (Phase 002).
- Any rule-based agent logic, severity classification, or alerts (Phase 003+).
- Notification log rows or notification message construction (Phase 005).
- Genie AI context enrichment (Phase 007).
- Any external email, Teams, Slack, or webhook notification (Phase 008).
- Pairing/deduplication logic across multiple commits, multi-row or multi-order changes.
- Monitoring tables other than confirming they are untouched.
- Production scheduling, jobs, or migration (Phase 009).

## Acceptance Criteria Summary

- [ ] Source table existence and Delta format confirmed before any change.
- [ ] Current CDF status checked and reported.
- [ ] CDF enabled (`delta.enableChangeDataFeed = true`) and confirmed.
- [ ] Enable step is idempotent (safe to re-run).
- [ ] Baseline commit version captured before the test update and displayed.
- [ ] Test update increases `sls_price` by 15% for `SO43697` only; rows-affected reported.
- [ ] `table_changes()` from baseline returns `update_preimage` and `update_postimage` rows for `SO43697`.
- [ ] Old price and new price extracted and displayed.
- [ ] Commit version of the change displayed.
- [ ] Overall validation status (PASS/FAIL) displayed.
- [ ] No change events, alerts, notification logs, Genie, or external notifications created.
- [ ] All steps run in serverless Free Edition with no external dependencies.
