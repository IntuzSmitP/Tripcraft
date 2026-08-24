"""
Tests for AgentState — persistence, tool results, assumptions.
"""

import pytest

from app.models.state import AgentState, Assumption, ToolResultEntry, BudgetTracker


class TestAgentState:
    def test_initial_state(self):
        state = AgentState(goal="Test trip")

        assert state.goal == "Test trip"
        assert state.status == "planning"
        assert state.iterations == 0
        assert len(state.tool_results) == 0
        assert len(state.execution_log) == 0
        assert len(state.assumptions) == 0

    def test_add_log(self):
        state = AgentState()
        entry = state.add_log("PLAN", "Starting plan")

        assert entry.step == 1
        assert entry.action == "PLAN"
        assert entry.detail == "Starting plan"
        assert len(state.execution_log) == 1

    def test_multiple_log_entries_sequential_steps(self):
        state = AgentState()
        state.add_log("PLAN", "Step 1")
        state.add_log("TOOL", "Step 2")
        state.add_log("RESULT", "Step 3")

        assert len(state.execution_log) == 3
        assert [e.step for e in state.execution_log] == [1, 2, 3]

    def test_tool_results_persist(self):
        """Core requirement: tool results must NOT disappear after a tool call."""
        state = AgentState()

        state.add_tool_result("search_flights", {"origin": "A"}, {"price": 5000})
        state.add_tool_result("search_hotels", {"city": "B"}, {"price": 1200})

        assert len(state.tool_results) == 2
        assert state.tool_results[0].tool_name == "search_flights"
        assert state.tool_results[1].tool_name == "search_hotels"

        # Results are still accessible
        assert state.tool_results[0].result["price"] == 5000
        assert state.tool_results[1].result["price"] == 1200

    def test_get_tool_result_returns_most_recent(self):
        state = AgentState()
        state.add_tool_result("search_flights", {}, {"price": 5000})
        state.add_tool_result("search_flights", {}, {"price": 3000})

        result = state.get_tool_result("search_flights")
        assert result is not None
        assert result["price"] == 3000  # Most recent

    def test_get_tool_result_returns_none_for_missing(self):
        state = AgentState()
        assert state.get_tool_result("nonexistent") is None

    def test_assumptions_tracking(self):
        state = AgentState()
        a = state.add_assumption("flight_cost_estimate", 5000)

        assert a.key == "flight_cost_estimate"
        assert a.value == 5000
        assert a.invalidated is False

    def test_assumption_invalidation(self):
        """Self-correction: assumptions can be marked invalid."""
        state = AgentState()
        state.add_assumption("flight_cost_estimate", 5000)

        state.invalidate_assumption(
            "flight_cost_estimate",
            "Actual flight costs ₹11,500",
        )

        a = state.assumptions[0]
        assert a.invalidated is True
        assert "11,500" in a.invalidated_reason

    def test_budget_tracker(self):
        budget = BudgetTracker(total=15000, currency="INR")
        budget.breakdown["flights"] = 8500
        budget.spent = sum(budget.breakdown.values())
        budget.remaining = budget.total - budget.spent

        assert budget.remaining == 6500
        assert budget.breakdown["flights"] == 8500

    def test_state_serializable(self):
        """State must be JSON-serializable for the state inspector."""
        state = AgentState(goal="Test")
        state.add_log("PLAN", "Start")
        state.add_tool_result("test", {"a": 1}, {"b": 2})
        state.add_assumption("test_key", 42)
        state.budget.total = 15000

        data = state.model_dump()
        assert isinstance(data, dict)
        assert data["goal"] == "Test"
        assert len(data["execution_log"]) == 1
        assert len(data["tool_results"]) == 1


class TestToolResultEntry:
    def test_creation(self):
        entry = ToolResultEntry(
            tool_name="search_flights",
            arguments={"origin": "Ahmedabad"},
            result={"price": 5000},
        )
        assert entry.tool_name == "search_flights"
        assert entry.timestamp is not None
