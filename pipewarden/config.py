"""Configuration loader and validator for pipewarden."""

import os
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class AlertRule:
    name: str
    metric: str
    operator: str
    threshold: float
    severity: str = "warning"

    VALID_OPERATORS = ("gt", "lt", "gte", "lte", "eq")
    VALID_SEVERITIES = ("info", "warning", "critical")

    def __post_init__(self):
        if self.operator not in self.VALID_OPERATORS:
            raise ValueError(
                f"Invalid operator '{self.operator}'. Must be one of {self.VALID_OPERATORS}"
            )
        if self.severity not in self.VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{self.severity}'. Must be one of {self.VALID_SEVERITIES}"
            )


@dataclass
class PipewardenConfig:
    pipeline_name: str
    alert_rules: list[AlertRule] = field(default_factory=list)
    check_interval_seconds: int = 60
    log_level: str = "INFO"


def load_config(config_path: str) -> PipewardenConfig:
    """Load and parse a YAML configuration file into a PipewardenConfig object."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    if not raw:
        raise ValueError("Config file is empty or invalid YAML.")

    if "pipeline_name" not in raw:
        raise ValueError("Config must include 'pipeline_name'.")

    rules = [
        AlertRule(
            name=r["name"],
            metric=r["metric"],
            operator=r["operator"],
            threshold=float(r["threshold"]),
            severity=r.get("severity", "warning"),
        )
        for r in raw.get("alert_rules", [])
    ]

    return PipewardenConfig(
        pipeline_name=raw["pipeline_name"],
        alert_rules=rules,
        check_interval_seconds=raw.get("check_interval_seconds", 60),
        log_level=raw.get("log_level", "INFO"),
    )
