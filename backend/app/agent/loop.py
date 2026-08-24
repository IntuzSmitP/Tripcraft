"""
Core agent loop — the heart of TripCraft.

Implements the autonomous planning loop:
    User Goal → LLM → Tool Call? → Execute → Store → LLM → … → Final Plan

Uses LangChain for LLM interaction. Provider switching and fallbacks
are handled automatically by LangChain (see app/agent/llm.py).

Message types:
  - SystemMessage   — system prompt
  - HumanMessage    — user / tool results
  - AIMessage       — model response (may contain tool_calls)
  - ToolMessage     — result of a tool call
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.agent.llm import create_llm
from app.agent.prompts import build_state_summary, build_system_prompt
from app.agent.tool_registry import ToolRegistry
from app.config import settings
from app.models.plan import FinalOutput
from app.models.state import AgentState, ExecutionLogEntry

logger = logging.getLogger(__name__)


async def run_agent_stream(
    goal: str,
    registry: ToolRegistry,
    state: AgentState | None = None,
) -> AsyncGenerator[ExecutionLogEntry, None]:
    """
    Run the agent loop, yielding ExecutionLogEntry items as they happen.

    This is the core function used by the SSE endpoint for real-time streaming.
    """
    if state is None:
        state = AgentState(goal=goal)
    else:
        state.goal = goal

    state.status = "planning"
    max_iterations = settings.max_agent_iterations

    # Build LangChain LLM with tools and fallbacks
    lc_tools = registry.get_langchain_tools()
    llm = create_llm(lc_tools)

    # Conversation history (LangChain messages)
    messages: list[BaseMessage] = [HumanMessage(content=goal)]

    # Initial log
    entry = state.add_log("PLAN", f"Received goal: {goal}")
    yield entry

    final_output: FinalOutput | None = None

    while state.iterations < max_iterations and state.status == "planning":
        state.iterations += 1
        logger.info("Agent iteration %d/%d", state.iterations, max_iterations)

        # ── Build system prompt with current state ──────────────
        state_summary = build_state_summary(
            goal=state.goal,
            constraints=state.constraints,
            tool_results=[tr.model_dump() for tr in state.tool_results],
            assumptions=[a.model_dump() for a in state.assumptions],
            budget=state.budget.model_dump(),
            iterations=state.iterations,
        )
        system_prompt = build_system_prompt(
            default_origin=settings.default_origin,
            state_summary=state_summary,
        )

        # Full message list = system prompt + conversation history
        full_messages: list[BaseMessage] = [
            SystemMessage(content=system_prompt),
            *messages,
        ]

        # ── Call LLM (with automatic provider fallback) ─────────
        try:
            response: AIMessage = await llm.ainvoke(full_messages)  # type: ignore[assignment]
        except Exception as e:
            entry = state.add_log("ERROR", f"LLM call failed: {e}")
            yield entry
            state.status = "error"
            break

        # Add model response to conversation history
        messages.append(response)

        # ── Handle tool calls ───────────────────────────────────
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name: str = tc["name"]
                tool_args: dict = tc["args"]
                tool_call_id: str = tc.get("id") or tool_name

                # Log the tool call
                args_str = ", ".join(f'{k}="{v}"' for k, v in tool_args.items())
                entry = state.add_log("TOOL", f"{tool_name}({args_str})")
                yield entry

                # ── ask_user: pause and wait for input ──────────
                if tool_name == "ask_user":
                    state.status = "waiting_for_user"
                    question = tool_args.get("question", "Awaiting user input...")
                    entry = state.add_log("WAITING", question)
                    yield entry

                    while state.status == "waiting_for_user":
                        await asyncio.sleep(0.5)

                    user_reply = state.user_input or ""
                    result_data = {"user_response": user_reply}
                    state.user_input = None

                    # Auto-capture budget if the user mentioned one and we don't have one yet
                    if state.budget.total <= 0:
                        found_budget = _extract_budget_from_text(user_reply)
                        if found_budget:
                            state.budget.total = found_budget
                            state.budget.remaining = found_budget
                            state.constraints["budget"] = found_budget
                            logger.info("Budget extracted from user reply: ₹%s", found_budget)
                else:
                    result_data = registry.execute(tool_name, tool_args)

                # Store result in state
                state.add_tool_result(tool_name, tool_args, result_data)

                # Log the result
                result_summary = _summarise_tool_result(tool_name, result_data)
                entry = state.add_log("RESULT", result_summary)
                yield entry

                # Budget impact check
                correction_entry = _check_budget_impact(state, tool_name, result_data)
                if correction_entry:
                    yield correction_entry

                # Add tool result to conversation history
                import json
                messages.append(ToolMessage(
                    content=json.dumps(result_data, default=str),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                ))

            # Prompt the model to continue after providing tool results.
            # This prevents some models (like Gemini) from returning empty
            # responses immediately after a ToolMessage.
            messages.append(HumanMessage(
                content="Tool execution complete. Please continue planning based on these results."
            ))

            await asyncio.sleep(0.1)
            continue

        # ── Handle text (final answer) ──────────────────────────
        text = ""
        if isinstance(response.content, str):
            text = response.content
        elif isinstance(response.content, list):
            texts = []
            for block in response.content:
                if isinstance(block, str):
                    texts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
            text = "\n".join(texts)

        if text:
            parsed = _parse_final_json(text)
            if parsed:
                try:
                    final_output = FinalOutput(**parsed)
                    state.status = "completed"
                    state.current_plan = text

                    invalidated = [
                        a.invalidated_reason or f"{a.key} was invalidated"
                        for a in state.assumptions
                        if a.invalidated
                    ]
                    if invalidated and not final_output.assumptions_changed:
                        final_output.assumptions_changed = invalidated

                    if not final_output.execution_summary:
                        final_output.execution_summary = [e.detail for e in state.execution_log]

                    entry = state.add_log("FINAL", "Generated final travel plan.")
                    yield entry
                    break

                except Exception as e:
                    logger.warning("Failed to parse final output: %s", e)
                    entry = state.add_log("RE-EVALUATE", "Response format invalid, retrying.")
                    yield entry
                    messages.append(HumanMessage(
                        content="Your response was not valid JSON. Please respond with ONLY "
                                "the final JSON plan as specified in the instructions."
                    ))
                    continue
            else:
                # Model thinking out loud — keep going
                messages.append(HumanMessage(
                    content="Please continue. Provide the final JSON plan or call a tool."
                ))
                continue
        else:
            # Empty response
            logger.warning("LLM returned empty response. Raw response: %s", response)
            entry = state.add_log("RE-EVALUATE", "Empty response from LLM, retrying.")
            yield entry
            messages.append(HumanMessage(
                content="You returned an empty response. Please call a tool or provide the final JSON plan."
            ))
            await asyncio.sleep(1)
            continue

    # ── Max iterations guard ────────────────────────────────────
    if state.status == "planning":
        state.status = "error"
        entry = state.add_log(
            "FINAL",
            f"Reached maximum iterations ({max_iterations}) without completing the plan.",
        )
        yield entry


# ── Helpers ─────────────────────────────────────────────────────

def _parse_final_json(text: str) -> dict | None:
    """Try to parse JSON from the model text, stripping markdown fences if present."""
    import json
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = [ln for ln in cleaned.split("\n") if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse model text as JSON: %s...", cleaned[:200])
        return None


def _summarise_tool_result(tool_name: str, result: dict) -> str:
    """Create a concise human-readable summary of a tool result."""
    if "error" in result:
        return f"Error: {result['error']}"

    if tool_name == "ask_user":
        return f"User replied: {result.get('user_response', '')}"

    if tool_name == "search_flights":
        options = result.get("options", [])
        if options:
            cheapest = options[0]
            return (
                f"Found {len(options)} flights. "
                f"Cheapest: {cheapest.get('airline', 'Unknown')} at "
                f"₹{cheapest.get('price', '?'):,}"
            )
        return "No flights found."

    if tool_name == "search_hotels":
        options = result.get("options", [])
        if options:
            cheapest = options[0]
            return (
                f"Found {len(options)} hotels. "
                f"Cheapest: {cheapest.get('name', 'Unknown')} at "
                f"₹{cheapest.get('price_per_night', '?'):,}/night"
            )
        return "No hotels found within budget."

    if tool_name == "convert_currency":
        return (
            f"{result.get('amount', '?')} {result.get('from_currency', '?')} = "
            f"{result.get('converted_amount', '?')} {result.get('to_currency', '?')}"
        )

    if tool_name == "check_weather":
        return (
            f"{result.get('city', '?')}: {result.get('condition', '?')}, "
            f"{result.get('temperature_high_celsius', '?')}°C high, "
            f"{result.get('humidity_percent', '?')}% humidity"
        )

    import json
    return json.dumps(result, default=str)[:200]


def _check_budget_impact(
    state: AgentState, tool_name: str, result: dict,
) -> ExecutionLogEntry | None:
    """After a tool result, check if it impacts budget assumptions."""
    if tool_name == "search_flights" and "options" in result:
        options = result["options"]
        if not options:
            return None

        cheapest_price = options[0].get("price", 0)
        total_budget = state.budget.total

        if total_budget <= 0:
            return None

        return_flight_cost = cheapest_price * 2
        budget_ratio = return_flight_cost / total_budget

        if budget_ratio > 0.6:
            state.budget.breakdown["flights"] = return_flight_cost
            state.budget.spent = sum(state.budget.breakdown.values())
            state.budget.remaining = total_budget - state.budget.spent

            state.invalidate_assumption(
                "flight_cost_estimate",
                f"Actual cheapest return flight costs ₹{return_flight_cost:,}, "
                f"which is {budget_ratio:.0%} of the total ₹{total_budget:,} budget.",
            )

            return state.add_log(
                "RE-EVALUATE",
                f"Flight cost (₹{return_flight_cost:,} return) exceeds "
                f"{budget_ratio:.0%} of total budget ₹{total_budget:,}. "
                f"Remaining: ₹{state.budget.remaining:,}.",
            )

    if tool_name == "search_hotels" and "options" in result:
        options = result["options"]
        if options:
            cheapest = options[0]
            nights = max(state.constraints.get("duration_days", 3) - 1, 1)
            hotel_total = cheapest["price_per_night"] * nights
            state.budget.breakdown["hotels"] = hotel_total
            state.budget.spent = sum(state.budget.breakdown.values())
            state.budget.remaining = state.budget.total - state.budget.spent

    return None


def _extract_budget_from_text(text: str) -> float | None:
    """
    Try to extract a numeric budget from a free-text string.

    Recognises patterns like:
      ₹40,000  |  Rs.40000  |  40000 INR  |  1 lakh  |  budget is 40k
    """
    import re

    if not text:
        return None

    # Normalise to lowercase for keyword matching
    t = text.lower()

    # lakh / lac shorthand  (e.g. "1 lakh", "1.5 lakhs", "1lac")
    lakh_match = re.search(r'([\d]+(?:\.\d+)?)\s*(?:lakh|lac)s?', t)
    if lakh_match:
        return float(lakh_match.group(1)) * 100_000

    # k shorthand  (e.g. "40k", "40 k")
    k_match = re.search(r'([\d]+(?:\.\d+)?)\s*k\b', t)
    if k_match:
        return float(k_match.group(1)) * 1_000

    # Explicit currency patterns
    patterns = [
        r'₹\s*([\d,]+)',
        r'rs\.?\s*([\d,]+)',
        r'inr\s*([\d,]+)',
        r'([\d,]+)\s*(?:inr|rupees?)',
        r'budget\s*(?:is|of|:)?\s*₹?\s*([\d,]+)',
        r'under\s*₹?\s*([\d,]+)',
        r'within\s*₹?\s*([\d,]+)',
        # bare number ≥ 1000 as last resort
        r'\b([1-9][\d,]{3,})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                continue

    return None
