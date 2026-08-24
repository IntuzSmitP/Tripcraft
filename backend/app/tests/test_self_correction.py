"""
Tests for the deterministic self-correction scenario.

This tests the exact requirement from the spec:
1. Agent estimates flights at ₹5000
2. Agent calls search_flights for Goa (which deterministically returns ₹11,500)
3. The budget overrun is detected
4. The plan adjusts or reports infeasible
"""

import json

import pytest

from app.agent.loop import _check_budget_impact, run_agent
from app.agent.tool_registry import ToolRegistry
from app.models.state import AgentState
from app.tools.flights import search_flights
from app.tools.hotels import search_hotels
from app.tests.test_agent_loop import MockLLMClient


def test_budget_impact_detection():
    """Test the internal helper that detects budget violations."""
    state = AgentState(goal="Plan a 3-day trip to Goa under ₹15,000")
    state.budget.total = 15000
    state.constraints["duration_days"] = 3
    
    # Add an initial assumption
    state.add_assumption("flight_cost_estimate", 5000)

    # Simulate tool returning an expensive flight (₹11,500 one way = ₹23,000 return)
    # Wait, the Goa flight in the mock is ₹11,500 one way.
    # Return flight is ₹23,000, which exceeds the ₹15,000 budget entirely!
    tool_result = search_flights("Ahmedabad", "Goa", "2026-09-10")
    
    # Call the check function
    entry = _check_budget_impact(state, "search_flights", tool_result)
    
    assert entry is not None
    assert entry.action == "RE-EVALUATE"
    assert "exceeds" in entry.detail
    
    # The assumption should be marked invalid
    invalidated = [a for a in state.assumptions if a.invalidated]
    assert len(invalidated) == 1
    assert invalidated[0].key == "flight_cost_estimate"


@pytest.mark.asyncio
async def test_full_self_correction_scenario():
    """Test the full loop with the self-correction scenario."""
    registry = ToolRegistry()
    registry.register("search_flights", search_flights)
    registry.register("search_hotels", search_hotels)
    
    final_json = {
        "status": "infeasible",
        "reason": "Flight cost exceeds total budget",
        "assumptions_changed": ["Flight cost estimate was invalidated"]
    }

    mock_llm = MockLLMClient([
        # Turn 1: Flight search
        MockLLMClient._build_tool_response(
            "search_flights", {"origin": "Ahmedabad", "destination": "Goa", "date": "2026-09-10"}
        ),
        # Turn 2: The loop will inject a RE-EVALUATE state automatically due to the expensive flight.
        # The LLM sees the new state and decides it's infeasible without searching hotels.
        MockLLMClient._build_text_response(json.dumps(final_json)),
    ])

    state = AgentState(goal="Plan a 3-day trip to Goa under ₹15,000")
    state.budget.total = 15000
    state.add_assumption("flight_cost_estimate", 5000)

    final_state, final_output = await run_agent(
        goal="Plan a 3-day trip to Goa under ₹15,000",
        registry=registry,
        llm=mock_llm,
        state=state,
    )

    # Verify the state
    assert final_state.status == "completed"
    
    # Verify the assumption was invalidated
    invalidated = [a for a in final_state.assumptions if a.invalidated]
    assert len(invalidated) == 1
    assert "17,000" in invalidated[0].invalidated_reason
    
    # Verify the final output captured the change
    assert final_output.status == "infeasible"
    assert len(final_output.assumptions_changed) >= 1
    
    # Verify the execution log contains the re-evaluate step
    actions = [e.action for e in final_state.execution_log]
    assert "RE-EVALUATE" in actions
