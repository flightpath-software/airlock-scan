"""LLM backends for the Tier-2 quarantined reviewer.

We speak the OpenAI-compatible Chat Completions API so one client reaches cloud
and local providers alike (see :class:`code_scanner.config.LLMConfig`). The HTTP
client uses only the standard library — no SDK dependency — and is invoked only
when a real backend is configured. Tests use :class:`FakeBackend` and never touch
the network.

Safety (see docs/canary-tripwires.md §"how we ensure the review does no damage"):
we pass **only** our explicit tool list and never enable any provider built-in /
server-side tools. A returned tool call is inert data — the caller decides what,
if anything, to do with it.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ToolCall:
    name: str
    arguments: dict
    call_id: str = ""
    raw_arguments: str = ""


@dataclass(frozen=True, slots=True)
class BackendResponse:
    tool_calls: list[ToolCall] = field(default_factory=list)
    text: str = ""


class LLMBackend(Protocol):
    def complete(self, *, system: str, user: str, tools: list[dict]) -> BackendResponse:
        """Return the model's response given a system prompt, user content, tools."""
        ...


class BackendError(RuntimeError):
    """Raised when a real backend cannot be reached or returns garbage."""


class OpenAICompatBackend:
    """OpenAI-compatible Chat Completions client (stdlib HTTP)."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.timeout = timeout

    def complete(self, *, system: str, user: str, tools: list[dict]) -> BackendResponse:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "tools": tools,
            "tool_choice": "auto",
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(  # noqa: S310 - fixed https/http API endpoint
            f"{self.base_url}/chat/completions", data=data, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network path
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise BackendError(f"HTTP {exc.code} from {self.base_url}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:  # pragma: no cover
            raise BackendError(f"backend request failed: {exc}") from exc

        return _parse_chat_completion(body)


def _parse_chat_completion(body: dict) -> BackendResponse:
    choices = body.get("choices") or []
    if not choices:
        return BackendResponse()
    message = (choices[0] or {}).get("message", {}) or {}
    text = message.get("content") or ""
    calls: list[ToolCall] = []
    for tc in message.get("tool_calls") or []:
        fn = (tc or {}).get("function", {}) or {}
        name = fn.get("name") or ""
        raw = fn.get("arguments") or ""
        try:
            args = json.loads(raw) if isinstance(raw, str) and raw else (raw or {})
            if not isinstance(args, dict):
                args = {"_value": args}
        except json.JSONDecodeError:
            args = {"_unparsed": raw}
        calls.append(ToolCall(name=name, arguments=args, call_id=tc.get("id", ""), raw_arguments=raw))
    return BackendResponse(tool_calls=calls, text=text)


class FakeBackend:
    """Scripted backend for tests/offline runs. Never touches the network.

    ``responder`` maps ``(system, user, tools) -> BackendResponse``. The default
    responder simulates a clean reviewer that always calls ``submit_verdict``.
    """

    def __init__(
        self,
        responder: Callable[[str, str, list[dict]], BackendResponse] | None = None,
    ) -> None:
        self.responder = responder or _default_clean_responder
        self.calls: list[dict] = []

    def complete(self, *, system: str, user: str, tools: list[dict]) -> BackendResponse:
        self.calls.append({"system": system, "user": user, "tools": tools})
        return self.responder(system, user, tools)


def _default_clean_responder(system: str, user: str, tools: list[dict]) -> BackendResponse:
    return BackendResponse(
        tool_calls=[
            ToolCall(
                name="submit_verdict",
                arguments={
                    "contains_injection": False,
                    "confidence": 0.95,
                    "findings": [],
                    "summary": "no injection detected",
                },
            )
        ]
    )


def from_config(llm_cfg, *, api_key: str | None = None) -> LLMBackend:
    """Construct a real backend from an ``LLMConfig`` (see config.py)."""
    return OpenAICompatBackend(
        base_url=llm_cfg.effective_base_url,
        model=llm_cfg.effective_model,
        api_key=api_key,
        temperature=llm_cfg.temperature,
        timeout=llm_cfg.request_timeout,
    )
