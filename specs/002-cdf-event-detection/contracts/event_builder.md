# Contract: `src/cdf_agent_monitoring/event_builder.py`

Pure-Python module. **No Spark, no third-party deps** (standard library `json` only). Unit-testable with `pytest` on any machine.

## `calculate_change_percent(old_value, new_value) -> float | None`

Signed percentage change from `old_value` to `new_value`.

- Coerce both to `float`. If either is `None` → return `None`.
- If either cannot be coerced (non-numeric) → return `None`.
- If `old_value == 0` → return `None` (avoid divide-by-zero).
- Otherwise return `round(((new - old) / old) * 100, 2)`.

**Required test vectors** (in `tests/test_event_builder.py`):

| old | new | result |
|-----|-----|--------|
| 100 | 115 | 15 |
| 100 | 80  | -20 |
| 100 | 100 | 0 |
| 0   | 100 | None |
| None | 100 | None |
| 100 | None | None |
| "abc" | 100 | None (non-numeric) |

> Note: numeric strings (e.g., `"100"`) are valid and coerced; only non-numeric strings return `None`. Integer-valued results may be returned as `15.0`/`-20.0`/`0.0` — tests compare by numeric value.

## `build_business_key(row, key_columns) -> str`

Return a JSON object string mapping each business-key column to its value in `row`.

- `row`: a mapping (dict-like) supporting `row[col]`.
- Example: `build_business_key({"sls_ord_num": "SO43697"}, ["sls_ord_num"])` → `'{"sls_ord_num": "SO43697"}'`.
- Values are serialized as-is (stringify for stable output is acceptable; must be valid JSON).

## `build_json_from_columns(row, columns) -> str`

Return a JSON object string mapping each listed column to its value in `row`.

- Used for `context_json` with `["sls_prd_key", "sls_cust_id", "sls_quantity", "sls_sales"]`.
- Missing keys MUST be included in the JSON output with value `null`; assert this in a test.
- Output must be valid JSON parseable by `json.loads`.

## General

- Functions are side-effect free and deterministic.
- No reading of environment, files, or network.
