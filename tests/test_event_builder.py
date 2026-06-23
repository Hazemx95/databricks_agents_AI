import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cdf_agent_monitoring import config, event_builder


def test_event_builder_placeholder_imports_without_spark():
    assert event_builder.__doc__


def test_config_source_and_event_constants():
    assert config.SOURCE_TABLE == "databricks_arrow_cata.bronz.sales_info"
    assert config.MONITORING_SCHEMA == "databricks_arrow_cata.monitoring"
    assert config.EVENTS_TABLE == "databricks_arrow_cata.monitoring.change_events"
    assert config.WATCHED_COLUMN == "sls_price"
    assert config.BUSINESS_KEY_COLUMNS == ["sls_ord_num"]
