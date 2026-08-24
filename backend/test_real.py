"""
Quick smoke-test for the agent loop.

Supplies realistic answers when the agent asks questions so it can
actually complete a planning session without burning extra API calls.
"""
import asyncio
from app.agent.loop import run_agent_stream
from app.agent.tool_registry import ToolRegistry
from app.tools.flights import search_flights
from app.tools.hotels import search_hotels
from app.tools.weather import check_weather
from app.tools.currency import convert_currency
from app.tools.human import ask_user
from app.models.state import AgentState


def _answer_for(question: str) -> str:
    """Return a sensible answer based on what the AI asked."""
    q = question.lower()
    if "budget" in q and "date" in q:
        return "My travel dates are 28th September 2026 and my budget is ₹40,000."
    if "budget" in q:
        return "My budget is ₹40,000."
    if "date" in q or "when" in q or "travel" in q:
        return "28th September 2026."
    if "origin" in q or "from" in q or "depart" in q:
        return "Ahmedabad."
    # Generic fallback
    return "28th September 2026 with a budget of ₹40,000."


async def main():
    registry = ToolRegistry()
    registry.register("search_flights", search_flights)
    registry.register("search_hotels", search_hotels)
    registry.register("convert_currency", convert_currency)
    registry.register("check_weather", check_weather)
    registry.register("ask_user", ask_user)

    state = AgentState(goal="plan a trip to kerala from ahmedabad for 10 days")

    print(f"\n{'='*60}")
    print(f"Goal: {state.goal}")
    print(f"{'='*60}\n")

    async for entry in run_agent_stream(state.goal, registry, state):
        print(f"Step {entry.step:>2}: [{entry.action:<12}] {entry.detail}")
        if state.status == "waiting_for_user":
            # Find the last WAITING log entry to get the question
            waiting_entries = [e for e in state.execution_log if e.action == "WAITING"]
            question = waiting_entries[-1].detail if waiting_entries else ""
            answer = _answer_for(question)
            print(f"        >> Auto-reply: {answer}")
            state.user_input = answer
            state.status = "planning"

    print(f"\n{'='*60}")
    print(f"Final status: {state.status}")
    print(f"Iterations used: {state.iterations}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
