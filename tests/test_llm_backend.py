"""Tests for the OpenAI-compatible response parser and the FakeBackend.

No network is touched: we parse a representative response body directly and use
the scripted FakeBackend.
"""

from __future__ import annotations

from code_scanner.llm_backend import (
    BackendResponse,
    FakeBackend,
    ToolCall,
    _parse_chat_completion,
)


def test_parse_tool_call_with_json_arguments():
    body = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "submit_verdict",
                                "arguments": '{"contains_injection": true, "confidence": 0.8, "summary": "bad"}',
                            },
                        }
                    ],
                }
            }
        ]
    }
    resp = _parse_chat_completion(body)
    assert len(resp.tool_calls) == 1
    tc = resp.tool_calls[0]
    assert tc.name == "submit_verdict"
    assert tc.arguments["contains_injection"] is True
    assert tc.call_id == "call_1"


def test_parse_handles_malformed_arguments():
    body = {
        "choices": [
            {"message": {"tool_calls": [{"function": {"name": "x", "arguments": "{not json"}}]}}
        ]
    }
    resp = _parse_chat_completion(body)
    assert resp.tool_calls[0].arguments == {"_unparsed": "{not json"}


def test_parse_text_only():
    body = {"choices": [{"message": {"content": "just text"}}]}
    resp = _parse_chat_completion(body)
    assert resp.text == "just text"
    assert resp.tool_calls == []


def test_fake_backend_records_calls_and_returns_default_clean():
    be = FakeBackend()
    resp = be.complete(system="s", user="u", tools=[])
    assert isinstance(resp, BackendResponse)
    assert resp.tool_calls[0].name == "submit_verdict"
    assert be.calls and be.calls[0]["user"] == "u"


def test_fake_backend_custom_responder():
    be = FakeBackend(lambda s, u, t: BackendResponse(tool_calls=[ToolCall("execute_shell", {})]))
    resp = be.complete(system="s", user="u", tools=[])
    assert resp.tool_calls[0].name == "execute_shell"
