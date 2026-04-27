"""Tests for pipewarden configuration loading and validation."""

import os
import textwrap

import pytest

from pipewarden.config import AlertRule, PipewardenConfig, load_config


@pytest.fixture
def valid_config_file(tmp_path):
    config_content = textwrap.dedent("""
        pipeline_name: test_pipeline
        check_interval_seconds: 45
        log_level: DEBUG
        alert_rules:
          - name: high_errors
            metric: error_rate
            operator: gt
            threshold: 10.0
            severity: critical
          - name: low_throughput
            metric: rps
            operator: lt
            threshold: 50
    """)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


def test_load_valid_config(valid_config_file):
    config = load_config(valid_config_file)
    assert isinstance(config, PipewardenConfig)
    assert config.pipeline_name == "test_pipeline"
    assert config.check_interval_seconds == 45
    assert config.log_level == "DEBUG"
    assert len(config.alert_rules) == 2


def test_alert_rule_defaults(valid_config_file):
    config = load_config(valid_config_file)
    low_throughput_rule = config.alert_rules[1]
    assert low_throughput_rule.severity == "warning"
    assert low_throughput_rule.threshold == 50.0


def test_alert_rule_severity_critical(valid_config_file):
    config = load_config(valid_config_file)
    assert config.alert_rules[0].severity == "critical"


def test_file_not_found():
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config("/nonexistent/path/config.yaml")


def test_missing_pipeline_name(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("log_level: INFO\n")
    with pytest.raises(ValueError, match="pipeline_name"):
        load_config(str(config_file))


def test_invalid_operator():
    with pytest.raises(ValueError, match="Invalid operator"):
        AlertRule(name="bad", metric="x", operator="neq", threshold=1.0)


def test_invalid_severity():
    with pytest.raises(ValueError, match="Invalid severity"):
        AlertRule(name="bad", metric="x", operator="gt", threshold=1.0, severity="urgent")


def test_empty_config_file(tmp_path):
    config_file = tmp_path / "empty.yaml"
    config_file.write_text("")
    with pytest.raises(ValueError, match="empty or invalid"):
        load_config(str(config_file))


@pytest.mark.parametrize("operator", ["gt", "lt", "gte", "lte", "eq"])
def test_valid_operators(operator):
    """Ensure all documented valid operators are accepted without error."""
    rule = AlertRule(name="test", metric="latency", operator=operator, threshold=1.0)
    assert rule.operator == operator
