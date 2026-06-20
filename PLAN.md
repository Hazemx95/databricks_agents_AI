# Databricks CDF Rule-Based AI Agent Monitoring Plan

## 1. Project Goal

Build a Databricks agentic monitoring workflow that detects important column changes in a Delta table using Delta Change Data Feed, converts those changes into structured event JSON, applies rule-based agent logic, writes alerts into audit tables, and optionally enriches notifications with Genie context.

The first implementation will run in Databricks Free Edition using serverless compute only.

## 2. Workspace and Catalog

Test catalog:

```text
databricks_arrow_cata
```

Source schema:

```text
bronz
```

Source table:

```text
databricks_arrow_cata.bronz.sales_info
```

Monitoring schema:

```text
databricks_arrow_cata.monitoring
```

## 3. Free Edition / Serverless Constraints

This project is first implemented in Databricks Free Edition.

Important constraints:

```text
- Compute is serverless only.
- No custom classic cluster configuration.
- External outbound internet access may be restricted.
- No hardcoded secrets.
- No personal API keys.
- External email / Teams / Slack / webhook notification is deferred until confirmed supported and approved.
```

First notification target:

```text
databricks_arrow_cata.monitoring.notification_log
```

So in the first POC, “send notification” means:

```text
Write a notification/audit row into a Delta table.
```

External notification comes later.

## 4. Source Table Columns

Confirmed source table columns:

```text
sls_ord_num
sls_prd_key
sls_cust_id
sls_order_dt
sls_ship_dt
sls_due_dt
sls_sales
sls_quantity
sls_price
_rescued_data
_source_file_path
_source_file_name
_source_file_size
_source_file_modification_time
_ingest_ts
_source_system
_source_schema
_source_table
```

## 5. First Business Event

Event name:

```text
SALES_PRICE_CHANGE
```

Business meaning:

```text
Detect when sls_price changes for a sales order.
```

First business key:

```text
sls_ord_num
```

Context columns:

```text
sls_prd_key
sls_cust_id
sls_quantity
sls_sales
```

Watched column:

```text
sls_price
```

Optional later watched column:

```text
sls_sales
```

## 6. First Event Example

Example detected change:

```json
{
  "event_type": "SALES_PRICE_CHANGE",
  "source_table": "databricks_arrow_cata.bronz.sales_info",
  "business_key": {
    "sls_ord_num": "SO43697"
  },
  "context": {
    "sls_prd_key": "BK-R93R-62",
    "sls_cust_id": "21768",
    "sls_quantity": "1",
    "sls_sales": "3578"
  },
  "watched_column": "sls_price",
  "old_value": "3578",
  "new_value": "4000",
  "change_percent": 11.8,
  "commit_version": 12,
  "commit_timestamp": "2026-06-20T10:30:00"
}
```

## 7. Rule-Based Agent Behavior

The first version is a:

```text
Rule-Based Databricks Data Agent
```

The agent does not use an LLM in the first POC.

The agent will:

```text
1. Receive event JSON.
2. Check configured thresholds.
3. Classify severity.
4. Decide whether notification is required.
5. Write alert row.
6. Write notification log row.
7. Update alert status.
```

## 8. First Rule

Rule ID:

```text
SALES_PRICE_CHANGE_001
```

Rule logic:

```text
If ABS(change_percent) >= 10 → HIGH
If ABS(change_percent) >= 5  → MEDIUM
If ABS(change_percent) < 5   → LOW
```

Notification logic for first POC:

```text
HIGH    → create alert + notification log
MEDIUM  → create alert + notification log
LOW     → create alert only / audit only
```

No external email/Teams/webhook in the first POC.

## 9. Target Monitoring Tables

Create the following managed Delta tables under:

```text
databricks_arrow_cata.monitoring
```

Required tables:

```text
agent_rules
change_events
agent_alerts
notification_log
agent_run_log
```

## 10. Phase Plan

### Phase 000 — Project Bootstrap and Table Discovery

Goal:

Prepare project structure and confirm source table capabilities.

Scope:

```text
- Create local project structure.
- Add PLAN.md.
- Confirm source table exists.
- Confirm table is Delta.
- Confirm current table properties.
- Confirm CDF is not enabled yet.
- Create monitoring schema.
- Create monitoring tables.
```

Source table:

```text
databricks_arrow_cata.bronz.sales_info
```

SQL checks:

```sql
DESCRIBE TABLE databricks_arrow_cata.bronz.sales_info;

DESCRIBE DETAIL databricks_arrow_cata.bronz.sales_info;

DESCRIBE HISTORY databricks_arrow_cata.bronz.sales_info;

SHOW TBLPROPERTIES databricks_arrow_cata.bronz.sales_info;
```

Acceptance criteria:

```text
- Project structure exists locally.
- Source table is queryable.
- Source table format is confirmed as Delta.
- Monitoring schema exists.
- Monitoring tables exist.
- CDF status is documented as not enabled yet.
```

Out of scope:

```text
- Do not enable CDF yet.
- Do not run CDF detection yet.
- Do not create test update yet.
- Do not send external notification.
```

---

## Genie AI Context Requirement

Although the first working implementation uses a rule-based agent without an external LLM, the project must support Genie AI context enrichment.

Genie will be used after the rule-based alert is created. The role of Genie is not to detect changes. The role of Genie is to enrich the alert with business context from Unity Catalog tables.

The agent will ask Genie questions such as:

- What is the product/customer context for this sales order?
- Show recent price history for this product key.
- Is the new price unusual compared with recent values?
- Summarize the business impact of this change.

The workflow must store Genie output in:

`databricks_arrow_cata.monitoring.agent_alerts.genie_context_json`

If Genie is unavailable, the workflow must still succeed and create the alert/notification using rule-based logic only.

### Phase 001 — Enable and Validate Change Data Feed

Goal:

Enable Delta Change Data Feed on:

```text
databricks_arrow_cata.bronz.sales_info
```

Scope:

```text
- Enable CDF using ALTER TABLE.
- Confirm CDF table property.
- Capture current table version as baseline.
- Create safe test update for one row.
- Validate table_changes() returns update_preimage and update_postimage.
```

Enable CDF:

```sql
ALTER TABLE databricks_arrow_cata.bronz.sales_info
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
```

Recommended test update:

```sql
UPDATE databricks_arrow_cata.bronz.sales_info
SET sls_price = sls_price * 1.15
WHERE sls_ord_num = 'SO43697';
```

Validation query:

```sql
SELECT
  sls_ord_num,
  sls_prd_key,
  sls_cust_id,
  sls_sales,
  sls_quantity,
  sls_price,
  _change_type,
  _commit_version,
  _commit_timestamp
FROM table_changes('databricks_arrow_cata.bronz.sales_info', <baseline_version>)
WHERE sls_ord_num = 'SO43697'
ORDER BY _commit_version, _change_type;
```

Acceptance criteria:

```text
- CDF is enabled.
- Test update succeeds.
- table_changes() returns update_preimage and update_postimage.
- Old sls_price and new sls_price can be seen.
```

Out of scope:

```text
- No rule-based agent yet.
- No notification log yet.
- No Genie yet.
```

---

### Phase 002 — Build CDF Change Event Detection

Goal:

Detect `sls_price` changes and write structured events.

Scope:

```text
- Read CDF rows from baseline version.
- Filter update_preimage and update_postimage rows.
- Pair old/new rows using sls_ord_num and _commit_version.
- Compare old sls_price vs new sls_price.
- Calculate change_percent.
- Write event to change_events table.
```

Business key:

```text
sls_ord_num
```

Context columns:

```text
sls_prd_key
sls_cust_id
sls_quantity
sls_sales
```

Watched column:

```text
sls_price
```

Acceptance criteria:

```text
- One price update creates one event row.
- Event includes old_value, new_value, change_percent.
- Event includes commit_version and commit_timestamp.
- Duplicate events are prevented for same rule_id, sls_ord_num, watched_column, and commit_version.
```

Out of scope:

```text
- No external notification.
- No Genie.
```

---

### Phase 003 — Monitoring Rules Table

Goal:

Store monitoring behavior in `agent_rules`.

First rule:

```text
rule_id: SALES_PRICE_CHANGE_001
rule_name: Sales price change monitoring
catalog_name: databricks_arrow_cata
schema_name: bronz
table_name: sales_info
business_key_columns: sls_ord_num
context_columns: sls_prd_key,sls_cust_id,sls_quantity,sls_sales
watched_column: sls_price
condition_type: percent_change
medium_threshold_percent: 5
high_threshold_percent: 10
notification_target_type: alert_table
notification_target_value: databricks_arrow_cata.monitoring.notification_log
is_active: true
```

Acceptance criteria:

```text
- First rule exists in agent_rules.
- Rule can be loaded by workflow.
- Rule values match real source columns.
```

---

### Phase 004 — Rule-Based Agent

Goal:

Create the first agent layer without LLM.

Scope:

```text
- Read new events from change_events.
- Apply rule thresholds.
- Classify severity: HIGH, MEDIUM, LOW.
- Decide should_notify.
- Write result to agent_alerts.
```

Agent decision example:

```json
{
  "agent_type": "RULE_BASED_AGENT",
  "severity": "HIGH",
  "should_notify": true,
  "reason": "sls_price changed by 15%, which exceeds the high threshold of 10%.",
  "recommended_action": "Review this sales price change."
}
```

Acceptance criteria:

```text
- HIGH alert is created when change_percent >= 10.
- MEDIUM alert is created when change_percent >= 5.
- LOW alert is audit only.
- Alert links back to event_id and rule_id.
```

---

### Phase 005 — Notification Log

Goal:

Create internal notification record.

Scope:

```text
- Build notification subject/body.
- Insert notification into notification_log.
- Update alert_status.
```

First POC notification type:

```text
ALERT_TABLE_ONLY
```

Example notification body:

```text
[HIGH] Sales price changed for order SO43697.

Product: BK-R93R-62
Customer ID: 21768
Old price: 3578
New price: 4114.70
Change: +15.00%

Recommended action:
Review this sales price change.
```

Acceptance criteria:

```text
- HIGH and MEDIUM alerts create notification_log rows.
- Notification body is readable.
- Alert status is updated to NOTIFICATION_LOGGED.
```

---

### Phase 006 — End-to-End Workflow Notebook

Goal:

Create one notebook/script to run the full POC.

Execution order:

```text
1. Load active rule.
2. Read CDF from baseline/start version.
3. Build change event.
4. Run rule-based agent.
5. Write alert.
6. Write notification log.
7. Update statuses.
8. Show output tables.
```

Acceptance criteria:

```text
- One test update creates one event.
- One event creates one alert.
- One alert creates one notification log.
- Re-running does not duplicate event/alert/notification.
```

---

### Phase 007 — Optional Genie Context

Goal:

Add Genie context after base POC works.

Scope:

```text
- Ask Genie context questions for HIGH alerts.
- Store Genie result in genie_context_json.
- Add Genie result to notification message if available.
```

Example Genie questions:

```text
What is the product and sales context for product key BK-R93R-62?
Show recent sales price history for product BK-R93R-62.
Is this price change unusual compared with recent sales?
```

Acceptance criteria:

```text
- Genie enrichment is optional.
- If Genie is unavailable, workflow still succeeds.
- No external OpenAI API key is required in this phase.
```

---

### Phase 008 — External Notification

Goal:

Add email/Teams/webhook only after workspace capability and approval.

Scope:

```text
- Use Databricks secrets.
- No hardcoded credentials.
- Add one approved target only.
- Log delivery success/failure.
```

Acceptance criteria:

```text
- External notification works in approved environment.
- Failure does not remove audit records.
- Secrets are never printed.
```

---

### Phase 009 — Production Migration

Goal:

Prepare migration from Free Edition/test workspace to production workspace.

Scope:

```text
- Review CDF retention.
- Review Unity Catalog permissions.
- Review managed location/schema ownership.
- Review workflow scheduling.
- Review external notification policy.
- Review audit and monitoring.
```

Acceptance criteria:

```text
- Production deployment checklist exists.
- Required permissions are documented.
- Tables and jobs can be recreated in production catalog.
```

## 11. First Implementation Values

Use these constants in the first code version:

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

## 12. First Branches

```text
feature/000-project-bootstrap
feature/001-enable-cdf
feature/002-cdf-event-detection
feature/003-agent-rules
feature/004-rule-based-agent
feature/005-notification-log
feature/006-end-to-end-workflow
feature/007-genie-context
feature/008-external-notification
feature/009-production-migration
```

## 13. Not Included in First POC

```text
- LangChain
- OpenAI API
- Full LLM agent
- RAG
- External email/Teams/webhook
- Multi-table monitoring
- Production scheduling
```

## 14. First POC Definition of Done

The first POC is complete when:

```text
1. CDF is enabled on databricks_arrow_cata.bronz.sales_info.
2. A test update changes sls_price for sls_ord_num = SO43697.
3. table_changes() returns update_preimage and update_postimage.
4. Workflow creates one row in change_events.
5. Rule-based agent creates one row in agent_alerts.
6. Notification log creates one row in notification_log.
7. Re-running does not duplicate rows.
```
