"""
Integration tests for the core agent loop.

Uses a mocked LangChain LLM to simulate deterministic sequences of
tool calls and final text outputs without hitting any real API.
"""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.loop import run_agent_stream
from app.agent.tool_registry import ToolRegistry
from app.models.state import AgentState
from app.tools.flights import search_flights
from app.tools.hotels import search_hotels


# ── Mock LangChain LLM ──────────────────────────────────────────

def _make_tool_call_response(name: str, args: dict[str, Any]) -> MagicMock:
    """Return a mock AIMessage with a tool call."""
    tc = MagicMock()
    tc.id = f"call_{name}"
    tc.function.name = name
    tc.function.arguments = json.dumps(args)

    msg = MagicMock()
    msg.tool_calls = [{"name": name, "args": args, "id": f"call_{name}"}]
    msg.content = None
    return msg


def _make_text_response(text: str) -> MagicMock:
    """Return a mock AIMessage with text content and no tool calls."""
    msg = MagicMock()
    msg.tool_calls = []
    msg.content = text
    return msg


def build_mock_llm(responses: list[Any]):
    """Build a mock LangChain LLM that returns responses in sequence."""
    call_count = {"n": 0}

    async def ainvoke(messages, **kwargs):
        idx = call_count["n"]
        call_count["n"] += 1
        if idx >= len(responses):
            return _make_text_response("{}")
        return responses[idx]

    mock = AsyncMock()
    mock.ainvoke = ainvoke
    return mock


# ── Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def registry():
    reg = ToolRegistry()
    reg.register("search_flights", search_flights)
    reg.register("search_hotels", search_hotels)
    return reg


# ── Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_single_tool_then_finish(registry, monkeypatch):
    """Agent calls one tool then returns a final JSON plan."""
    final_json = {"trip": {"destination": "Mumbai"}, "status": "feasible"}

    mock_llm = build_mock_llm([
        _make_tool_call_response("search_flights", {"origin": "Ahmedabad", "destination": "Mumbai", "date": "2026-10-01"}),
        _make_text_response(json.dumps(final_json)),
    ])

    # Patch create_llm so the loop uses our mock
    monkeypatch.setattr("app.agent.loop.create_llm", lambda tools: mock_llm)

    state = AgentState(goal="Go to Mumbai")
    entries = []
    async for entry in run_agent_stream("Go to Mumbai", registry, state):
        entries.append(entry)

    assert state.status == "completed"
    assert state.iterations == 2
    assert len(state.tool_results) == 1
    assert state.tool_results[0].tool_name == "search_flights"


@pytest.mark.asyncio
async def test_agent_multiple_tools(registry, monkeypatch):
    """Agent makes multiple sequential tool calls then finishes."""
    final_json = {"status": "feasible"}

    mock_llm = build_mock_llm([
        _make_tool_call_response("search_flights", {"origin": "Ahmedabad", "destination": "Delhi", "date": "2026-10-01"}),
        _make_tool_call_response("search_hotels", {"city": "Delhi", "budget": 3000.0}),
        _make_text_response(json.dumps(final_json)),
    ])

    monkeypatch.setattr("app.agent.loop.create_llm", lambda tools: mock_llm)

    state = AgentState(goal="Go to Delhi")
    async for _ in run_agent_stream("Go to Delhi", registry, state):
        pass

    assert state.status == "completed"
    assert len(state.tool_results) == 2
    assert state.tool_results[0].tool_name == "search_flights"
    assert state.tool_results[1].tool_name == "search_hotels"


@pytest.mark.asyncio
async def test_agent_max_iterations(registry, monkeypatch):
    """Loop terminates gracefully when max iterations is reached."""
    monkeypatch.setattr("app.agent.loop.settings.max_agent_iterations", 2)

    mock_llm = build_mock_llm([
        _make_tool_call_response("search_flights", {"origin": "X", "destination": "Y", "date": "Z"}),
        _make_tool_call_response("search_flights", {"origin": "X", "destination": "Y", "date": "Z"}),
        _make_tool_call_response("search_flights", {"origin": "X", "destination": "Y", "date": "Z"}),
    ])

    monkeypatch.setattr("app.agent.loop.create_llm", lambda tools: mock_llm)

    state = AgentState(goal="Infinite loop")
    async for _ in run_agent_stream("Infinite loop", registry, state):
        pass

    assert state.status == "error"
    assert state.iterations == 2
    last_log = state.execution_log[-1]
    assert "maximum iterations" in last_log.detail.lower()
