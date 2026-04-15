"""Tests for You.com search tool registration."""

import io
import json

from agent_harness import get_registry, register_you_com_search_tool


def test_you_search_tool_requires_api_key(monkeypatch):
    get_registry().clear()
    monkeypatch.delenv("YDC_API_KEY", raising=False)
    monkeypatch.delenv("YOUCOM_API_KEY", raising=False)

    register_you_com_search_tool(name="you_search_test")
    tool = get_registry().get("you_search_test")

    result = tool.callable("latest ai agent frameworks")
    assert "not configured" in result.lower()


def test_you_search_tool_formats_results(monkeypatch):
    get_registry().clear()
    monkeypatch.setenv("YDC_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            payload = {
                "results": {
                    "web": [
                        {
                            "title": "Agent blog",
                            "url": "https://example.com/agent",
                            "description": "Generic page summary.",
                            "snippets": ["Useful update.", "Fresh context."],
                        }
                    ]
                }
            }
            self._buf = io.BytesIO(json.dumps(payload).encode("utf-8"))
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self._buf.read()

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())

    register_you_com_search_tool(name="you_search_test")
    tool = get_registry().get("you_search_test")

    result = tool.callable("agent tooling", num_results=1)
    assert "1. Agent blog" in result
    assert "https://example.com/agent" in result
    assert "Useful update. Fresh context." in result
    assert "Generic page summary." not in result


def test_you_search_tool_supports_legacy_api_key_alias(monkeypatch):
    get_registry().clear()
    monkeypatch.delenv("YDC_API_KEY", raising=False)
    monkeypatch.setenv("YOUCOM_API_KEY", "legacy-key")

    class FakeResponse:
        def __enter__(self):
            payload = {
                "results": {
                    "web": [
                        {
                            "title": "Legacy alias hit",
                            "url": "https://example.com/legacy",
                            "snippets": ["Alias still works."],
                        }
                    ]
                }
            }
            self._buf = io.BytesIO(json.dumps(payload).encode("utf-8"))
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self._buf.read()

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())

    register_you_com_search_tool(name="you_search_test")
    tool = get_registry().get("you_search_test")

    result = tool.callable("agent tooling", num_results=1)
    assert "Legacy alias hit" in result
