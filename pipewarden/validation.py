"""Schema and value validation for pipeline check results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationRule:
    """A single validation rule applied to a named field."""

    field: str
    rule: str  # 'required', 'min', 'max', 'type', 'regex'
    value: Optional[Any] = None
    message: Optional[str] = None

    def __post_init__(self) -> None:
        allowed = {"required", "min", "max", "type", "regex"}
        if self.rule not in allowed:
            raise ValueError(f"Unknown rule '{self.rule}'. Must be one of {allowed}.")

    def __str__(self) -> str:
        return f"ValidationRule(field={self.field!r}, rule={self.rule!r}, value={self.value!r})"


@dataclass
class ValidationViolation:
    """Describes a single rule violation."""

    field: str
    rule: str
    message: str

    def __str__(self) -> str:
        return f"[{self.field}] {self.rule}: {self.message}"


@dataclass
class ValidationResult:
    """Aggregated outcome of validating a data record."""

    pipeline: str
    violations: List[ValidationViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def __str__(self) -> str:
        status = "PASS" if self.passed else f"FAIL ({len(self.violations)} violation(s))"
        return f"ValidationResult(pipeline={self.pipeline!r}, status={status})"


def validate(pipeline: str, record: Dict[str, Any], rules: List[ValidationRule]) -> ValidationResult:
    """Apply *rules* to *record* and return a ValidationResult."""
    import re

    violations: List[ValidationViolation] = []

    for rule in rules:
        raw = record.get(rule.field)

        if rule.rule == "required":
            if raw is None or raw == "":
                msg = rule.message or f"Field '{rule.field}' is required."
                violations.append(ValidationViolation(rule.field, rule.rule, msg))

        elif rule.rule == "min":
            if raw is not None and raw < rule.value:
                msg = rule.message or f"Field '{rule.field}' must be >= {rule.value}, got {raw}."
                violations.append(ValidationViolation(rule.field, rule.rule, msg))

        elif rule.rule == "max":
            if raw is not None and raw > rule.value:
                msg = rule.message or f"Field '{rule.field}' must be <= {rule.value}, got {raw}."
                violations.append(ValidationViolation(rule.field, rule.rule, msg))

        elif rule.rule == "type":
            type_map = {"int": int, "float": float, "str": str, "bool": bool}
            expected = type_map.get(rule.value)
            if expected and raw is not None and not isinstance(raw, expected):
                msg = rule.message or f"Field '{rule.field}' must be {rule.value}, got {type(raw).__name__}."
                violations.append(ValidationViolation(rule.field, rule.rule, msg))

        elif rule.rule == "regex":
            if raw is not None and not re.fullmatch(str(rule.value), str(raw)):
                msg = rule.message or f"Field '{rule.field}' does not match pattern '{rule.value}'."
                violations.append(ValidationViolation(rule.field, rule.rule, msg))

    return ValidationResult(pipeline=pipeline, violations=violations)
