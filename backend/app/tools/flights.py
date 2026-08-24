"""
Mock flight search tool.

The Goa route deliberately returns expensive flights to trigger
the agent's self-correction logic — this is the deterministic
scenario required by the spec.
"""

from __future__ import annotations


# ── Route-specific mock data ────────────────────────────────────

_FLIGHT_DATA: dict[str, list[dict]] = {
    "goa": [
        {"airline": "SkyHigh Air", "price": 11500, "duration_hours": 1.5},
        {"airline": "MockJet", "price": 9800, "duration_hours": 2.0},
        {"airline": "BudgetWings", "price": 8500, "duration_hours": 2.5},
    ],
    "mumbai": [
        {"airline": "MockAir", "price": 3200, "duration_hours": 1.0},
        {"airline": "SkyHigh Air", "price": 4100, "duration_hours": 1.25},
    ],
    "delhi": [
        {"airline": "MockAir", "price": 4500, "duration_hours": 2.0},
        {"airline": "BudgetWings", "price": 3800, "duration_hours": 2.5},
    ],
    "bangalore": [
        {"airline": "SkyHigh Air", "price": 5200, "duration_hours": 2.0},
        {"airline": "MockJet", "price": 4800, "duration_hours": 2.25},
    ],
    "jaipur": [
        {"airline": "MockAir", "price": 3500, "duration_hours": 1.5},
        {"airline": "BudgetWings", "price": 2900, "duration_hours": 2.0},
    ],
    "kolkata": [
        {"airline": "MockAir", "price": 5800, "duration_hours": 2.5},
        {"airline": "SkyHigh Air", "price": 6200, "duration_hours": 2.0},
    ],
}

# Default flights for unknown destinations
_DEFAULT_FLIGHTS = [
    {"airline": "MockAir", "price": 5000, "duration_hours": 2.0},
    {"airline": "BudgetWings", "price": 4200, "duration_hours": 2.5},
]


def search_flights(origin: str, destination: str, date: str) -> dict:
    """
    Search for available flights between two cities on a given date.

    Args:
        origin: Departure city name (e.g. "Ahmedabad").
        destination: Arrival city name (e.g. "Goa").
        date: Travel date in YYYY-MM-DD format (e.g. "2026-09-10").

    Returns:
        A dict containing origin, destination, date, and a list of
        flight options with airline, price (INR), and duration.
    """
    key = destination.strip().lower()
    options = _FLIGHT_DATA.get(key, _DEFAULT_FLIGHTS)

    return {
        "origin": origin.strip().title(),
        "destination": destination.strip().title(),
        "date": date,
        "currency": "INR",
        "options": sorted(options, key=lambda x: x["price"]),
    }
