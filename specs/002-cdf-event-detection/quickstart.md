# Quickstart: CDF Event Detection (Phase 002)

Validation guide proving CDF→event detection works end-to-end. See [data-model.md](./data-model.md) and [contracts/](./contracts/) for details.

## Prerequisites

- Databricks Free Edition workspace reachable via Databricks MCP or DEFAULT `.databrickscfg` profile; serverless compute available.
- Phase 000 tables exist (incl. `databricks_arrow_cata.monitoring.change_events`).
- Phase 001 done: CDF enabled on `databricks_arrow_cata.bronz.sales_info` (confirmed: `delta.enableChangeDataFeed = true`).
- At least one committed `sls_price` update exists in the source CDF history (Phase 001's validation update qualifies). If none exists, the notebook correctly prints "no new events".

## 1. Unit-test the helpers (local, no Databricks)

```bash
cd /home/hazem/databricks_agents_AI
python -m pytest tests/test_event_builder.py -q
```

**Expected**: all tests pass, including `100→115 ⇒ 15`, `100→80 ⇒ -20`, `100→100 ⇒ 0`, `0→100 ⇒ None`, null ⇒ `None`, non-numeric ⇒ `None`.

## 2. Run the detection notebook (live workspace)

Run `notebooks/02_run_cdf_detection.py` on serverless. Set widgets:
- `start_version` = `0` (or a known baseline)
- `end_version` = (leave empty to read to latest)

**Expected display sequence**: raw CDF rows → paired old/new rows → built event rows → final `change_events` rows for `SALES_PRICE_CHANGE_001`.

**Expected status**: `SUCCESS` with the count of newly written events when a price change exists; otherwise a clear "no new events" message.

## 3. Verify the events landed

```sql
SELECT event_id, rule_id, business_key_json, old_value, new_value,
       change_percent, watched_column, commit_version, commit_timestamp
FROM databricks_arrow_cata.monitoring.change_events
WHERE rule_id = 'SALES_PRICE_CHANGE_001'
ORDER BY commit_version;
```

**Expected**: one row per (order, commit) price change; valid JSON in `business_key_json`/`context_json`; `change_percent` matches `((new-old)/old)*100`.

## 4. Verify idempotency (the key acceptance test)

Run the notebook a **second time** with the same widget values, then:

```sql
SELECT rule_id, business_key_json, watched_column, commit_version, COUNT(*) AS n
FROM databricks_arrow_cata.monitoring.change_events
WHERE rule_id = 'SALES_PRICE_CHANGE_001'
GROUP BY rule_id, business_key_json, watched_column, commit_version
HAVING COUNT(*) > 1;
```

**Expected**: zero rows returned (no duplicates), and the total `change_events` count is unchanged from step 3. The second run prints the "no new events" message.

## Done when

- Helper unit tests pass locally.
- Notebook runs on serverless, displays all four stages, and prints an unambiguous status.
- Events for `SALES_PRICE_CHANGE_001` are present and schema-valid.
- A second identical run inserts zero rows (idempotent).
