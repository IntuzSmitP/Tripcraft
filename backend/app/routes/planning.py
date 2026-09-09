"""
REST and SSE controllers for the planning lifecycle.

Exposes endpoints for initiating asynchronous planning sessions, 
streaming real-time execution logs via Server-Sent Events (SSE), 
and retrieving the final serialized trip plan or full state dumps.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agent.loop import run_agent_stream, _parse_final_json, _extract_budget_from_text as _extract_budget_from_goal
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

# Auth

security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Validate Bearer token against the configured API token."""
    if credentials.credentials != settings.api_bearer_token:
        raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")
    return credentials.credentials


# In-memory session store

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


# Request / Response models


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


# Endpoints


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
    if len(_sessions) >= 500:
        # Simple cleanup of done sessions first
        done_keys = [k for k, v in _sessions.items() if v.get("done")]
        for k in done_keys:
            del _sessions[k]
        
        # If still full, reject
        if len(_sessions) >= 500:
            raise HTTPException(status_code=429, detail="Too many active planning sessions. Please try again later.")

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
    session_id: str = Path(..., max_length=50),
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
    session_id: str = Path(..., max_length=50),
    _token: str = Depends(verify_token),
) -> dict:
    """Return the full agent state for debugging / inspection."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state: AgentState = _sessions[session_id]["state"]
    return state.model_dump()


@router.get("/plan/{session_id}/result")
async def get_result(
    session_id: str = Path(..., max_length=50),
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


@router.get("/plan/{session_id}/hotels")
async def get_hotels(
    session_id: str = Path(..., max_length=50),
    _token: str = Depends(verify_token),
) -> dict:
    """Return all hotel options scraped during the session, organized by city."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = _sessions[session_id]
    state: AgentState = session["state"]
    
    cities_map: dict[str, list[dict]] = {}
    all_hotels: list[dict] = []
    
    for tr in state.tool_results:
        if tr.tool_name == "search_hotels" and isinstance(tr.result, dict):
            city_name = tr.result.get("city") or "Destination"
            options = tr.result.get("options", [])
            
            if city_name not in cities_map:
                cities_map[city_name] = []
                
            for opt in options:
                opt_copy = dict(opt)
                opt_copy["city"] = city_name
                cities_map[city_name].append(opt_copy)
                all_hotels.append(opt_copy)
                
    return {
        "hotels": all_hotels,
        "by_city": cities_map,
        "cities": list(cities_map.keys())
    }


class HotelUpdateRequest(BaseModel):
    hotel_name: str
    city: str | None = None
    
@router.patch("/plan/{session_id}/hotel")
async def update_hotel(
    request: HotelUpdateRequest,
    session_id: str = Path(..., max_length=50),
    _token: str = Depends(verify_token),
) -> dict:
    """Update the selected hotel for a completed plan."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = _sessions[session_id]
    state: AgentState = session["state"]
    output = session.get("output")
    
    if not output:
        raise HTTPException(status_code=400, detail="Plan not yet completed")
        
    # Find the hotel in tool results across all cities
    target_hotel = None
    hotel_city = None
    city_nights = None
    for tr in state.tool_results:
        if tr.tool_name == "search_hotels" and isinstance(tr.result, dict):
            c_name = tr.result.get("city")
            if request.city and c_name and c_name.lower() != request.city.lower():
                continue

            for h in tr.result.get("options", []):
                if h.get("name") == request.hotel_name:
                    target_hotel = h
                    hotel_city = c_name
                    city_nights = tr.result.get("nights")
                    break
            if target_hotel:
                break
                
    if not target_hotel:
        raise HTTPException(status_code=404, detail="Hotel not found in session options")
        
    # How many nights?
    nights = city_nights or max(state.constraints.get("duration_days", 3) - 1, 1)
    
    # Calculate new price
    price_per_night = target_hotel.get("price_per_night", 0)
    total_price = price_per_night * nights
    
    # Update hotel info in output
    from app.models.plan import HotelInfo
    
    new_hotel = HotelInfo(
        name=target_hotel.get("name"),
        city=hotel_city or target_hotel.get("location"),
        price_per_night=price_per_night,
        total_price=total_price,
        nights=nights,
        rating=target_hotel.get("rating"),
        currency="INR"
    )

    # Initialize / update output.hotels list
    existing_hotels = []
    if isinstance(output.hotels, list) and output.hotels:
        for h in output.hotels:
            h_dict = h.model_dump() if hasattr(h, "model_dump") else dict(h)
            existing_hotels.append(h_dict)
    elif output.hotel:
        h_dict = output.hotel.model_dump() if hasattr(output.hotel, "model_dump") else dict(output.hotel)
        if h_dict.get("name"):
            existing_hotels.append(h_dict)

    # Check if a hotel for hotel_city already exists in existing_hotels
    updated_hotels = []
    replaced = False
    for h in existing_hotels:
        h_city = h.get("city")
        if not replaced and ((h_city and hotel_city and h_city.lower() == hotel_city.lower()) or not h_city or not hotel_city or len(existing_hotels) == 1):
            updated_hotels.append(new_hotel.model_dump())
            replaced = True
        else:
            updated_hotels.append(h)
            
    if not replaced:
        updated_hotels.append(new_hotel.model_dump())
        
    output.hotels = [HotelInfo(**h) for h in updated_hotels]
    output.hotel = new_hotel
    
    # Recalculate total hotel costs across all selected hotels
    total_hotels_cost = sum(h.get("total_price", 0) for h in updated_hotels)
    
    # Update budget
    if isinstance(output.budget, BaseModel):
        if output.budget.breakdown is not None:
            output.budget.breakdown["hotels"] = total_hotels_cost
            output.budget.estimated = sum(output.budget.breakdown.values())
    elif isinstance(output.budget, dict):
        bd = output.budget.get("breakdown", {})
        bd["hotels"] = total_hotels_cost
        output.budget["breakdown"] = bd
        output.budget["estimated"] = sum(bd.values())
        
    # Update state budget to match
    state.budget.breakdown["hotels"] = total_hotels_cost
    state.budget.spent = sum(state.budget.breakdown.values())
    state.budget.remaining = state.budget.total - state.budget.spent
    
    # Add an execution log entry indicating manual change
    state.add_log("MANUAL_UPDATE", f"User updated hotel for {hotel_city or 'stay'} to {target_hotel.get('name')}")
    if isinstance(output.execution_summary, list):
        output.execution_summary.append(f"User changed accommodation for {hotel_city or 'stay'} to {target_hotel.get('name')}")
        
    return output.model_dump() if hasattr(output, "model_dump") else output


class UserInputRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=500, description="The user's answer to the agent's question")


@router.post("/plan/{session_id}/input")
async def provide_user_input(
    request: UserInputRequest,
    session_id: str = Path(..., max_length=50),
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


# Background task


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

        if final_output:
            _normalize_hotels(final_output, state)

        session["output"] = final_output

    except Exception as e:
        from app.agent.error_messages import friendly_error
        logger.exception("Planning session %s failed", session_id)
        state.status = "error"
        state.add_log("ERROR", friendly_error(e))

    finally:
        session["done"] = True


# Helper extractors


from app.agent.loop import _extract_budget_from_text as _extract_budget_from_goal


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


def _normalize_hotels(output: FinalOutput, state: AgentState) -> None:
    """Ensure output.hotels is cleanly populated for every searched city."""
    if not output:
        return
        
    city_options: dict[str, list[dict]] = {}
    city_nights: dict[str, int] = {}
    
    for tr in state.tool_results:
        if tr.tool_name == "search_hotels" and isinstance(tr.result, dict):
            c_name = tr.result.get("city") or "Destination"
            opts = tr.result.get("options", [])
            nights = tr.result.get("nights", 1)
            if opts:
                city_options[c_name] = opts
                city_nights[c_name] = nights
                
    if not city_options:
        return
        
    from app.models.plan import HotelInfo

    selected_hotels: list[HotelInfo] = []
    
    llm_text = ""
    if isinstance(output.hotel, BaseModel) and output.hotel.name:
        llm_text += output.hotel.name + " "
    elif isinstance(output.hotel, dict) and output.hotel.get("name"):
        llm_text += str(output.hotel.get("name")) + " "
    if isinstance(output.execution_summary, list):
        llm_text += " ".join(output.execution_summary)
        
    for c_name, opts in city_options.items():
        matched_opt = None
        for opt in opts:
            h_name = opt.get("name", "")
            if h_name and h_name.lower() in llm_text.lower():
                matched_opt = opt
                break
                
        if not matched_opt:
            matched_opt = opts[0]
            
        nights = city_nights.get(c_name, 1)
        price_per_night = matched_opt.get("price_per_night", 0)
        total_price = price_per_night * nights
        
        h_info = HotelInfo(
            name=matched_opt.get("name"),
            city=c_name,
            price_per_night=price_per_night,
            total_price=total_price,
            nights=nights,
            rating=matched_opt.get("rating"),
            currency="INR"
        )
        selected_hotels.append(h_info)
        
    output.hotels = selected_hotels
    if selected_hotels:
        output.hotel = selected_hotels[0]
        
    total_hotel_cost = sum(h.total_price or 0 for h in selected_hotels)
    if isinstance(output.budget, BaseModel):
        if output.budget.breakdown is not None:
            output.budget.breakdown["hotels"] = total_hotel_cost
            output.budget.estimated = sum(output.budget.breakdown.values())
    elif isinstance(output.budget, dict):
        bd = output.budget.get("breakdown", {})
        bd["hotels"] = total_hotel_cost
        output.budget["breakdown"] = bd
        output.budget["estimated"] = sum(bd.values())
        
    state.budget.breakdown["hotels"] = total_hotel_cost
    state.budget.spent = sum(state.budget.breakdown.values())
    state.budget.remaining = state.budget.total - state.budget.spent

