"""
End-to-end tests for the agent's self-correction capabilities when hitting budget constraints.

Validates the core requirements around budget overrun detection and handling:
1. Initial low estimation (e.g., ₹5000 for flights)
2. Tool execution retrieving higher actual cost (e.g., ₹11,500)
3. Budget overrun detection triggering plan adjustment or infeasibility reporting
"""

import json

import pytest

from app.agent.loop import _check_budget_impact, run_agent_stream
from app.agent.tool_registry import ToolRegistry
from app.models.state import AgentState
from app.tools.flights import search_flights
from app.tools.hotels import search_hotels
from app.tests.test_agent_loop import build_mock_llm, _make_tool_call_response, _make_text_response


def test_budget_impact_detection():
    """Validates the budget impact detection logic against an unexpected cost increase."""
    state = AgentState(goal="Plan a 3-day trip to Goa under ₹15,000")
    state.budget.total = 15000
    state.constraints["duration_days"] = 3
    
    # Seed the state with an optimistic initial assumption for flight costs
    state.add_assumption("flight_cost_estimate", 5000)

    # Simulate a real-world scenario where the actual flight cost is significantly higher than estimated
    tool_result = search_flights("Ahmedabad", "Goa", "2026-09-10")
    
    # Run the budget evaluation logic and ensure it flags the discrepancy for re-evaluation
    entry = _check_budget_impact(state, "search_flights", tool_result)
    
    assert entry is not None
    assert entry.action == "RE-EVALUATE"
    assert "exceeds" in entry.detail
    
    # Verify that the system correctly identifies and invalidates the optimistic assumption
    invalidated = [a for a in state.assumptions if a.invalidated]
    assert len(invalidated) == 1
    assert invalidated[0].key == "flight_cost_estimate"


@pytest.mark.asyncio
async def test_full_self_correction_scenario(monkeypatch):
    """
    End-to-end integration test validating the agent's ability to self-correct
    when encountering a budget overrun during execution.
    """
    registry = ToolRegistry()
    registry.register("search_flights", search_flights)
    registry.register("search_hotels", search_hotels)
    
    final_json = {
        "trip": {"destination": "Goa", "duration_days": 3, "date": "2026-09-10", "origin": "Ahmedabad"},
        "budget": {"requested": 15000, "estimated": 25000, "currency": "INR"},
        "transport": {"mode": "flight", "airline": "IndiGo", "price": 11500, "duration_hours": 2, "date": "2026-09-10"},
        "hotel": {"name": "Backpacker's Nest", "price_per_night": 800, "total_price": 2400, "nights": 3, "rating": 3.2, "type": "budget"},
        "weather": {"condition": "monsoon", "temperature_high": 30, "temperature_low": 24, "humidity": 85, "recommendation": "carry umbrella"},
        "assumptions_changed": ["Flight cost estimate was invalidated"],
        "status": "infeasible",
        "reason": "Flight cost exceeds total budget",
        "suggestions": ["Try different dates"],
        "execution_summary": ["Flight search completed"]
    }

    mock_llm = build_mock_llm([
        # Turn 1: Flight search
        _make_tool_call_response(
            "search_flights", {"origin": "Ahmedabad", "destination": "Goa", "date": "2026-09-10"}
        ),
        # Turn 2: Final plan
        _make_text_response(json.dumps(final_json)),
    ])
    monkeypatch.setattr("app.agent.loop.create_llm", lambda tools: mock_llm)

    state = AgentState(goal="Plan a 3-day trip to Goa under ₹15,000")
    state.budget.total = 15000
    state.add_assumption("flight_cost_estimate", 5000)

    async for _ in run_agent_stream("Plan a 3-day trip to Goa under ₹15,000", registry, state):
        pass

    # Verify the agent successfully navigated the self-correction path
    assert state.status == "completed"
    
    # Ensure the root cause of the budget issue (the assumption) was tracked and invalidated
    invalidated = [a for a in state.assumptions if a.invalidated]
    assert len(invalidated) == 1
    
    # Confirm the execution log reflects the agent's decision to re-evaluate the plan
    actions = [e.action for e in state.execution_log]
    assert "RE-EVALUATE" in actions
