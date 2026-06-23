import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cdf_agent_monitoring import config, rule_based_agent


def test_rule_based_agent_placeholder_imports_without_spark():
    assert rule_based_agent.__doc__


def test_config_rule_constants():
    assert config.RULE_ID == "SALES_PRICE_CHANGE_001"
    assert config.MEDIUM_THRESHOLD_PERCENT == 5.0
    assert config.HIGH_THRESHOLD_PERCENT == 10.0
    assert config.RULES_TABLE == "databricks_arrow_cata.monitoring.agent_rules"
    assert config.ALERTS_TABLE == "databricks_arrow_cata.monitoring.agent_alerts"
    assert config.NOTIFICATION_LOG_TABLE == "databricks_arrow_cata.monitoring.notification_log"
    assert config.RUN_LOG_TABLE == "databricks_arrow_cata.monitoring.agent_run_log"
