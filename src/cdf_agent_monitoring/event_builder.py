"""Pure-Python helpers for building structured change event values."""

import json


def calculate_change_percent(old_value, new_value):
    """Return signed percent change rounded to 2 decimals, or None if undefined."""
    if old_value is None or new_value is None:
        return None

    try:
        old_number = float(old_value)
        new_number = float(new_value)
    except (TypeError, ValueError):
        return None

    if old_number == 0:
        return None

    return round(((new_number - old_number) / old_number) * 100, 2)


def _row_value(row, column):
    if hasattr(row, "asDict"):
        row = row.asDict()
    return row.get(column) if hasattr(row, "get") else row[column]


def build_business_key(row, key_columns):
    """Return JSON for the configured business-key columns."""
    return build_json_from_columns(row, key_columns)


def build_json_from_columns(row, columns):
    """Return JSON for selected columns, using null for missing mapping keys."""
    values = {}
    for column in columns:
        try:
            values[column] = _row_value(row, column)
        except KeyError:
            values[column] = None

    return json.dumps(values, sort_keys=True, default=str)
