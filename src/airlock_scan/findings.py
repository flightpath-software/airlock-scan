"""Unified finding model shared across every scanner adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Severity(IntEnum):
    """Ordered severity levels.

    Higher value == more severe, so levels can be compared directly
    (e.g. ``finding.severity >= Severity.HIGH``).
    """

    UNKNOWN = 0
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

    @classmethod
    def parse(cls, value: object) -> "Severity":
        """Best-effort mapping of arbitrary tool severity strings to a level."""
        if isinstance(value, Severity):
            return value
        if value is None:
            return cls.UNKNOWN
        text = str(value).strip().lower()
        mapping = {
            # SARIF levels
            "error": cls.HIGH,
            "warning": cls.MEDIUM,
            "note": cls.LOW,
            "none": cls.INFO,
            # common named levels
            "critical": cls.CRITICAL,
            "crit": cls.CRITICAL,
            "high": cls.HIGH,
            "moderate": cls.MEDIUM,
            "medium": cls.MEDIUM,
            "med": cls.MEDIUM,
            "low": cls.LOW,
            "info": cls.INFO,
            "informational": cls.INFO,
            "unknown": cls.UNKNOWN,
        }
        if text in mapping:
            return mapping[text]
        # Numeric severity (e.g. CVSS-ish or 0-5 scales).
        try:
            num = float(text)
        except ValueError:
            return cls.UNKNOWN
        if num >= 9:
            return cls.CRITICAL
        if num >= 7:
            return cls.HIGH
        if num >= 4:
            return cls.MEDIUM
        if num > 0:
            return cls.LOW
        return cls.INFO

    @property
    def label(self) -> str:
        return self.name.capitalize()


@dataclass(frozen=True, slots=True)
class Finding:
    """A single normalized finding from any scanner."""

    tool: str
    severity: Severity
    message: str
    rule_id: str | None = None
    file: str | None = None
    line: int | None = None
    extra: dict = field(default_factory=dict)

    @property
    def location(self) -> str:
        if not self.file:
            return "-"
        return f"{self.file}:{self.line}" if self.line else self.file

    def as_dict(self) -> dict:
        return {
            "tool": self.tool,
            "severity": self.severity.label,
            "message": self.message,
            "rule_id": self.rule_id,
            "file": self.file,
            "line": self.line,
            "extra": self.extra,
        }
