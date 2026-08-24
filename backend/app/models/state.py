"""
Agent state models — the persistent memory of a planning session.

Every field in AgentState is serialisable so the full state can be
returned as JSON for the frontend state inspector.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# ── Granular sub-models ─────────────────────────────────────────


class Assumption(BaseModel):
    """A single assumption the agent makes that may later be invalidated."""

    key: str = Field(..., description="Machine-readable key, e.g. 'flight_cost_estimate'")
    value: Any = Field(..., description="The assumed value")
    invalidated: bool = Field(default=False)
    invalidated_reason: str | None = Field(default=None)


class ToolResultEntry(BaseModel):
    """One tool invocation and its result, stored chronologically."""

    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionLogEntry(BaseModel):
    """A single visible step in the execution log (shown to the user)."""

    step: int
    action: str  # PLAN | TOOL | RESULT | RE-EVALUATE | FINAL
    detail: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BudgetTracker(BaseModel):
    """Tracks budget allocation and spending."""

    total: float = Field(default=0.0, description="User-specified total budget")
    spent: float = Field(default=0.0, description="Sum of committed costs")
    remaining: float = Field(default=0.0, description="total - spent")
    currency: str = Field(default="INR")
    breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Category → amount, e.g. {'flights': 11500, 'hotels': 2400}",
    )


# ── Main Agent State ────────────────────────────────────────────


class AgentState(BaseModel):
    """
    Complete in-memory state for one planning session.

    This object is the *single source of truth* for the agent loop.
    It is mutated after every tool call and LLM turn, and can be
    serialised at any point for debugging / the state inspector.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    goal: str = Field(default="")
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted constraints: destination, duration, budget, origin, dates …",
    )
    current_plan: str = Field(
        default="",
        description="Free-text summary of the plan so far",
    )
    tasks: list[str] = Field(
        default_factory=list,
        description="Remaining tasks the agent still needs to do",
    )
    tool_results: list[ToolResultEntry] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    budget: BudgetTracker = Field(default_factory=BudgetTracker)
    iterations: int = Field(default=0)
    execution_log: list[ExecutionLogEntry] = Field(default_factory=list)
    status: str = Field(
        default="planning",
        description="planning | waiting_for_user | completed | infeasible | error",
    )
    user_input: str | None = Field(
        default=None,
        description="Temporarily stores the user's response while the agent is paused",
    )

    # ── helpers ─────────────────────────────────────────────────

    def add_log(self, action: str, detail: str) -> ExecutionLogEntry:
        """Append an entry to the execution log and return it."""
        entry = ExecutionLogEntry(
            step=len(self.execution_log) + 1,
            action=action,
            detail=detail,
        )
        self.execution_log.append(entry)
        return entry

    def add_tool_result(self, tool_name: str, arguments: dict, result: dict) -> ToolResultEntry:
        """Persist a tool result in state."""
        entry = ToolResultEntry(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
        )
        self.tool_results.append(entry)
        return entry

    def add_assumption(self, key: str, value: Any) -> Assumption:
        """Record a new assumption."""
        assumption = Assumption(key=key, value=value)
        self.assumptions.append(assumption)
        return assumption

    def invalidate_assumption(self, key: str, reason: str) -> None:
        """Mark an assumption as invalidated."""
        for a in self.assumptions:
            if a.key == key and not a.invalidated:
                a.invalidated = True
                a.invalidated_reason = reason

    def get_tool_result(self, tool_name: str) -> dict[str, Any] | None:
        """Return the most recent result for a given tool, or None."""
        for entry in reversed(self.tool_results):
            if entry.tool_name == tool_name:
                return entry.result
        return None
