"""Canary tripwire registry and harness fingerprinting.

Canaries are *inert* fake tool definitions offered to the quarantined reviewer.
The reviewer's only sanctioned tool is ``submit_verdict``; it has no legitimate
reason to call any canary, so a fire is high-signal evidence of an attempted
indirect prompt injection (see docs/canary-tripwires.md).

This module is pure data + attribution logic — it never calls a model and has no
side effects. M2 turns these neutral definitions into provider-specific tool
schemas; M3/M4 consume :func:`attribute` to fingerprint which harness a fired
decoy was tailored for.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

_DATA_FILE = "harness_signatures.json"

# Bait descriptions per action class — written to look like the capability an
# injection would reach for. They are decoys; nothing implements them.
_ACTION_BAIT = {
    "read": "Read the contents of a file or directory.",
    "search": "Search files or code for a pattern.",
    "edit": "Create, modify, or delete a file.",
    "execute": "Run a shell command on the host.",
    "network": "Fetch a URL or perform an outbound web request.",
    "delegate": "Spawn a sub-agent to carry out a task.",
    "plan": "Record or update a task plan.",
    "mcp": "Invoke an MCP tool or resource.",
    "browser": "Drive a web browser.",
    "memory": "Persist information across sessions.",
    "other": "Perform an auxiliary action.",
}

# Harness-agnostic decoys: names an injection reaches for regardless of harness.
AGNOSTIC_CANARIES: tuple[tuple[str, str], ...] = (
    ("execute_shell", "execute"),
    ("read_file", "read"),
    ("read_environment", "read"),
    ("http_request", "network"),
    ("send_email", "network"),
    ("write_file", "edit"),
)


@dataclass(frozen=True, slots=True)
class CanaryTool:
    """A single inert decoy tool definition (provider-neutral)."""

    name: str
    description: str
    action_class: str
    source: str  # "agnostic" or "harness:<id>"
    harnesses: tuple[str, ...]  # harness ids that expose this name


@dataclass(frozen=True, slots=True)
class Attribution:
    """What a fired canary tells us about the targeted harness."""

    tool: str
    action_class: str | None
    harnesses_exposing: tuple[str, ...]   # all harnesses whose toolset includes the name
    fingerprint_harnesses: tuple[str, ...]  # harnesses listing it as a distinctive fingerprint
    specificity: str  # "harness-specific" | "narrowed" | "harness-agnostic" | "unknown"

    @property
    def fingerprints(self) -> str | None:
        """The single harness this fire points at, if unambiguous."""
        if self.specificity == "harness-specific" and len(self.fingerprint_harnesses) == 1:
            return self.fingerprint_harnesses[0]
        if self.specificity == "harness-specific" and len(self.harnesses_exposing) == 1:
            return self.harnesses_exposing[0]
        return None


@lru_cache(maxsize=1)
def load_signatures() -> dict:
    """Load the vendored harness-signature dataset (packaged JSON)."""
    text = resources.files("airlock_scan").joinpath("data", _DATA_FILE).read_text(encoding="utf-8")
    return json.loads(text)


def _harness(sigs: dict, harness_id: str) -> dict | None:
    for h in sigs.get("harnesses", []):
        if h.get("id") == harness_id:
            return h
    return None


def build_canary_set(
    harness_ids: tuple[str, ...] | list[str],
    *,
    include_agnostic: bool = True,
    sigs: dict | None = None,
) -> list[CanaryTool]:
    """Build the decoy tool set for the given harnesses (+ optional agnostic set).

    Names are de-duplicated: the first source to claim a name wins, but the full
    set of harnesses exposing that name is recorded for attribution.
    """
    sigs = sigs or load_signatures()
    by_name: dict[str, CanaryTool] = {}

    exposing = _compute_names_to_harnesses(sigs)

    for harness_id in harness_ids:
        h = _harness(sigs, harness_id)
        if not h:
            continue
        for tool in h.get("tools", []):
            name = tool.get("name")
            if not name or name in by_name:
                continue
            action_class = tool.get("action_class", "other")
            by_name[name] = CanaryTool(
                name=name,
                description=_ACTION_BAIT.get(action_class, _ACTION_BAIT["other"]),
                action_class=action_class,
                source=f"harness:{harness_id}",
                harnesses=tuple(sorted(exposing.get(name, (harness_id,)))),
            )

    if include_agnostic:
        for name, action_class in AGNOSTIC_CANARIES:
            if name in by_name:
                continue
            by_name[name] = CanaryTool(
                name=name,
                description=_ACTION_BAIT.get(action_class, _ACTION_BAIT["other"]),
                action_class=action_class,
                source="agnostic",
                harnesses=tuple(sorted(exposing.get(name, ()))),
            )

    return [by_name[n] for n in sorted(by_name)]


def attribute(tool_name: str, *, sigs: dict | None = None) -> Attribution:
    """Given a fired canary name, infer which harness the attack targeted."""
    sigs = sigs or load_signatures()
    exposing = _compute_names_to_harnesses(sigs)
    fingerprinting = _compute_names_to_fingerprint_harnesses(sigs)
    action = _name_action_class(sigs, tool_name)

    exposing_ids = tuple(sorted(exposing.get(tool_name, ())))
    fp_ids = tuple(sorted(fingerprinting.get(tool_name, ())))

    if len(fp_ids) == 1:
        specificity = "harness-specific"
    elif len(fp_ids) > 1:
        specificity = "narrowed"
    elif len(exposing_ids) == 1:
        specificity = "harness-specific"
    elif len(exposing_ids) > 1:
        specificity = "harness-agnostic"
    else:
        specificity = "unknown"

    return Attribution(
        tool=tool_name,
        action_class=action,
        harnesses_exposing=exposing_ids,
        fingerprint_harnesses=fp_ids,
        specificity=specificity,
    )


def _compute_names_to_harnesses(sigs: dict) -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {}
    for h in sigs.get("harnesses", []):
        hid = h.get("id", "")
        for tool in h.get("tools", []):
            name = tool.get("name")
            if name:
                out.setdefault(name, []).append(hid)
    return {k: tuple(v) for k, v in out.items()}


def _compute_names_to_fingerprint_harnesses(sigs: dict) -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {}
    for h in sigs.get("harnesses", []):
        hid = h.get("id", "")
        for name in h.get("fingerprint_tools", []) or []:
            out.setdefault(name, []).append(hid)
    return {k: tuple(v) for k, v in out.items()}


def _name_action_class(sigs: dict, tool_name: str) -> str | None:
    for h in sigs.get("harnesses", []):
        for tool in h.get("tools", []):
            if tool.get("name") == tool_name:
                return tool.get("action_class")
    for name, action_class in AGNOSTIC_CANARIES:
        if name == tool_name:
            return action_class
    return None
