# TripCraft Backend

This is the FastAPI backend for the TripCraft multi-step AI planning agent.
It uses the Google Gemini API with native function calling to autonomously plan travel.

## Architecture

```text
User Goal
   ↓
API (/api/plan)
   ↓
Agent Loop ───────→ Tool Registry
   │  ↑                  │
   │  │                  ↓
   │  └──────────  Mock Tools (flights, hotels, etc.)
   ↓                     │
LLM (Gemini) ←───────────┘
   │
   ↓
Final JSON Plan
```

The core agent loop lives in `app/agent/loop.py`. It uses a Pydantic `AgentState` object as the single source of truth, persisting tool results and tracking budget assumptions across multiple turns.

## Setup

1. Install dependencies using `uv` (it manages the virtual environment automatically):
```bash
uv sync
```

2. Copy the `.env.example` file and add your Gemini API key:
```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY
```

3. Run the server:
```bash
uv run uvicorn app.main:app --reload
```

## Testing

Run the test suite using pytest via uv:
```bash
uv run pytest app/tests/ -v
```

The tests cover normal execution, tool logic, state persistence, and the deterministic self-correction scenario (Goa flights exceeding the budget).
