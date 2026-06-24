import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cdf_agent_monitoring import config, event_builder


def test_calculate_change_percent_increase():
    assert event_builder.calculate_change_percent(100, 115) == 15


def test_calculate_change_percent_decrease():
    assert event_builder.calculate_change_percent(100, 80) == -20


def test_calculate_change_percent_unchanged():
    assert event_builder.calculate_change_percent(100, 100) == 0


def test_calculate_change_percent_old_zero_returns_none():
    assert event_builder.calculate_change_percent(0, 100) is None


def test_calculate_change_percent_null_value_returns_none():
    assert event_builder.calculate_change_percent(None, 100) is None
    assert event_builder.calculate_change_percent(100, None) is None


def test_calculate_change_percent_non_numeric_value_returns_none():
    assert event_builder.calculate_change_percent("abc", 100) is None


def test_build_business_key_returns_valid_json():
    result = event_builder.build_business_key({"sls_ord_num": "SO43697"}, ["sls_ord_num"])

    assert json.loads(result) == {"sls_ord_num": "SO43697"}


def test_build_json_from_columns_returns_selected_columns_with_missing_as_null():
    row = {"sls_prd_key": "BK-R93R-62", "sls_quantity": 1}

    result = event_builder.build_json_from_columns(row, ["sls_prd_key", "sls_quantity", "missing"])

    assert json.loads(result) == {
        "sls_prd_key": "BK-R93R-62",
        "sls_quantity": 1,
        "missing": None,
    }


def test_config_source_and_event_constants():
    assert config.SOURCE_TABLE == "databricks_arrow_cata.bronz.sales_info"
    assert config.MONITORING_SCHEMA == "databricks_arrow_cata.monitoring"
    assert config.EVENTS_TABLE == "databricks_arrow_cata.monitoring.change_events"
    assert config.WATCHED_COLUMN == "sls_price"
    assert config.BUSINESS_KEY_COLUMNS == ["sls_ord_num"]
