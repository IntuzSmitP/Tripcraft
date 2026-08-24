"""
Planning API routes.

Endpoints:
  POST /api/plan         — start a new planning session
  GET  /api/plan/{id}/stream  — SSE stream of execution log
  GET  /api/plan/{id}/state   — inspect full agent state
  GET  /api/plan/{id}/result  — get final structured output
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agent.loop import run_agent_stream, _parse_final_json
from app.agent.tool_registry import ToolRegistry
from app.config import settings
from app.models.plan import FinalOutput
from app.models.state import AgentState
from app.tools.flights import search_flights
from app.tools.hotels import search_hotels
from app.tools.currency import convert_currency
from app.tools.weather import check_weather
from app.tools.human import ask_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Planning"])

# ── Auth ────────────────────────────────────────────────────────

security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Validate Bearer token against the configured API token."""
    if credentials.credentials != settings.api_bearer_token:
        raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")
    return credentials.credentials


# ── In-memory session store ─────────────────────────────────────

_sessions: dict[str, dict[str, Any]] = {}


def _build_registry() -> ToolRegistry:
    """Create and populate a fresh tool registry."""
    registry = ToolRegistry()
    registry.register("search_flights", search_flights)
    registry.register("search_hotels", search_hotels)
    registry.register("convert_currency", convert_currency)
    registry.register("check_weather", check_weather)
    registry.register("ask_user", ask_user)
    return registry


# ── Request / Response models ───────────────────────────────────


class PlanRequest(BaseModel):
    goal: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Natural language travel goal",
        json_schema_extra={"example": "Plan a 3-day trip to Goa under ₹15,000"},
    )


class PlanStartResponse(BaseModel):
    session_id: str
    status: str
    message: str


# ── Endpoints ───────────────────────────────────────────────────


@router.post("/plan", response_model=PlanStartResponse)
async def start_plan(
    request: PlanRequest,
    _token: str = Depends(verify_token),
) -> PlanStartResponse:
    """
    Start a new trip planning session.

    The agent runs asynchronously. Use the /stream endpoint to
    follow progress in real time, or /result to get the final plan.
    """
    state = AgentState(goal=request.goal)
    session_id = state.id

    # Extract budget from goal for state tracking
    budget = _extract_budget_from_goal(request.goal)
    if budget:
        state.budget.total = budget
        state.budget.remaining = budget

    # Extract constraints
    constraints = _extract_constraints_from_goal(request.goal)
    state.constraints = constraints

    registry = _build_registry()

    # Store session references
    _sessions[session_id] = {
        "state": state,
        "registry": registry,
        "output": None,
        "done": False,
    }

    # Run agent in background
    asyncio.create_task(_run_planning_session(session_id, request.goal))

    return PlanStartResponse(
        session_id=session_id,
        status="started",
        message="Planning session started. Use /api/plan/{id}/stream for real-time updates.",
    )


@router.get("/plan/{session_id}/stream")
async def stream_execution_log(
    session_id: str,
    _token: str = Depends(verify_token),
) -> EventSourceResponse:
    """
    SSE stream of execution log entries for a planning session.

    Each event is a JSON-encoded ExecutionLogEntry.
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        session = _sessions[session_id]
        last_index = 0

        while True:
            state: AgentState = session["state"]
            log = state.execution_log

            # Yield any new entries
            while last_index < len(log):
                entry = log[last_index]
                yield {
                    "event": "log",
                    "data": json.dumps(entry.model_dump(), default=str),
                }
                last_index += 1

            # Check if done
            if session["done"]:
                # Yield final result
                output = session.get("output")
                if output:
                    yield {
                        "event": "result",
                        "data": json.dumps(
                            output.model_dump() if hasattr(output, "model_dump") else output,
                            default=str,
                        ),
                    }
                yield {"event": "done", "data": json.dumps({"status": state.status})}
                break

            await asyncio.sleep(0.3)

    return EventSourceResponse(event_generator())


@router.get("/plan/{session_id}/state")
async def get_state(
    session_id: str,
    _token: str = Depends(verify_token),
) -> dict:
    """Return the full agent state for debugging / inspection."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state: AgentState = _sessions[session_id]["state"]
    return state.model_dump()


@router.get("/plan/{session_id}/result")
async def get_result(
    session_id: str,
    _token: str = Depends(verify_token),
) -> dict:
    """Return the final structured travel plan."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    if not session["done"]:
        raise HTTPException(status_code=202, detail="Planning still in progress")

    output = session.get("output")
    if output is None:
        state: AgentState = session["state"]
        return {
            "status": state.status,
            "reason": "Agent did not produce a final plan",
            "execution_log": [e.model_dump() for e in state.execution_log],
        }

    if hasattr(output, "model_dump"):
        return output.model_dump()
    return output


class UserInputRequest(BaseModel):
    input: str = Field(..., min_length=1, description="The user's answer to the agent's question")


@router.post("/plan/{session_id}/input")
async def provide_user_input(
    session_id: str,
    request: UserInputRequest,
    _token: str = Depends(verify_token),
) -> dict:
    """Provide input to a suspended planning session waiting for user response."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    state: AgentState = session["state"]

    if state.status != "waiting_for_user":
        raise HTTPException(status_code=400, detail=f"Session is not waiting for user input. Current status: {state.status}")

    state.user_input = request.input
    state.status = "planning"

    return {"status": "resumed", "message": "Input received, agent is resuming."}


# ── Background task ─────────────────────────────────────────────


async def _run_planning_session(session_id: str, goal: str) -> None:
    """Background task that runs the agent loop."""
    session = _sessions[session_id]
    state = session["state"]
    registry = session["registry"]

    try:
        final_output: FinalOutput | None = None
        async for entry in run_agent_stream(goal, registry, state):
            logger.info("[%s] Step %d: %s — %s", session_id, entry.step, entry.action, entry.detail)

        # Check if agent produced a plan (stored on state)
        if state.status == "completed" and state.current_plan:
            parsed = _parse_final_json(state.current_plan)
            if parsed:
                try:
                    final_output = FinalOutput(**parsed)
                except Exception:
                    final_output = FinalOutput(**{k: v for k, v in parsed.items() if k in FinalOutput.model_fields})

        session["output"] = final_output

    except Exception as e:
        logger.exception("Planning session %s failed", session_id)
        state.status = "error"
        state.add_log("ERROR", f"Planning failed: {str(e)}")

    finally:
        session["done"] = True


# ── Helper extractors ───────────────────────────────────────────


def _extract_budget_from_goal(goal: str) -> float | None:
    """Try to extract a numeric budget from the goal string."""
    import re

    # Match patterns like ₹15,000 or ₹15000 or 15000 INR or Rs.15000
    patterns = [
        r'₹\s*([\d,]+)',
        r'Rs\.?\s*([\d,]+)',
        r'INR\s*([\d,]+)',
        r'([\d,]+)\s*(?:INR|rupees?)',
        r'budget\s*(?:of|:)?\s*₹?\s*([\d,]+)',
        r'under\s*₹?\s*([\d,]+)',
        r'within\s*₹?\s*([\d,]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, goal, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                return float(amount_str)
            except ValueError:
                continue

    return None


def _extract_constraints_from_goal(goal: str) -> dict[str, Any]:
    """Extract basic constraints from the goal (best-effort)."""
    import re

    constraints: dict[str, Any] = {}

    # Duration
    duration_match = re.search(r'(\d+)\s*-?\s*day', goal, re.IGNORECASE)
    if duration_match:
        constraints["duration_days"] = int(duration_match.group(1))

    # Budget
    budget = _extract_budget_from_goal(goal)
    if budget:
        constraints["budget"] = budget
        constraints["currency"] = "INR"

    return constraints
