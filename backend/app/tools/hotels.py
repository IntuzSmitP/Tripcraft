"""
Mock hotel search tool.

Returns hotels filtered by a per-night budget ceiling.
"""

from __future__ import annotations


_HOTEL_DATA: dict[str, list[dict]] = {
    "goa": [
        {"name": "Backpacker's Nest", "price_per_night": 800, "rating": 3.2, "type": "hostel"},
        {"name": "Seaside Budget Inn", "price_per_night": 1200, "rating": 3.8, "type": "budget"},
        {"name": "Coastal Comfort", "price_per_night": 2500, "rating": 4.1, "type": "mid-range"},
        {"name": "Goa Grand Resort", "price_per_night": 5500, "rating": 4.6, "type": "luxury"},
        {"name": "Palm Beach Suites", "price_per_night": 8000, "rating": 4.8, "type": "premium"},
    ],
    "mumbai": [
        {"name": "City Lodge", "price_per_night": 1500, "rating": 3.5, "type": "budget"},
        {"name": "Marine Drive Stay", "price_per_night": 3500, "rating": 4.2, "type": "mid-range"},
        {"name": "The Taj Mock", "price_per_night": 12000, "rating": 4.9, "type": "luxury"},
    ],
    "delhi": [
        {"name": "Metro Inn", "price_per_night": 1000, "rating": 3.3, "type": "budget"},
        {"name": "Capital Comfort", "price_per_night": 2800, "rating": 4.0, "type": "mid-range"},
        {"name": "Imperial Mock", "price_per_night": 9500, "rating": 4.7, "type": "luxury"},
    ],
    "bangalore": [
        {"name": "Tech Park Stay", "price_per_night": 1800, "rating": 3.6, "type": "budget"},
        {"name": "Garden City Inn", "price_per_night": 3200, "rating": 4.1, "type": "mid-range"},
    ],
    "jaipur": [
        {"name": "Pink City Hostel", "price_per_night": 600, "rating": 3.0, "type": "hostel"},
        {"name": "Hawa Mahal View", "price_per_night": 1800, "rating": 3.9, "type": "budget"},
        {"name": "Royal Heritage", "price_per_night": 4500, "rating": 4.5, "type": "luxury"},
    ],
    "kolkata": [
        {"name": "Park Street Lodge", "price_per_night": 1100, "rating": 3.4, "type": "budget"},
        {"name": "Howrah Comfort", "price_per_night": 2200, "rating": 3.8, "type": "mid-range"},
    ],
}

_DEFAULT_HOTELS = [
    {"name": "Budget Stay", "price_per_night": 1500, "rating": 3.5, "type": "budget"},
    {"name": "Comfort Inn", "price_per_night": 3000, "rating": 4.0, "type": "mid-range"},
]


def search_hotels(city: str, budget: float | None = None) -> dict:
    """
    Search for hotels in a city within an optional per-night budget.

    Args:
        city: City name to search hotels in (e.g. "Goa").
        budget: Maximum price per night in INR (optional).

    Returns:
        A dict containing city, budget, currency, and a list of
        matching hotels with name, price_per_night, rating, and type.
    """
    key = city.strip().lower()
    try:
        budget_limit = float(budget) if budget is not None else float('inf')
    except (ValueError, TypeError):
        budget_limit = float('inf')
        
    all_hotels = _HOTEL_DATA.get(key, _DEFAULT_HOTELS)

    matching = [h for h in all_hotels if h["price_per_night"] <= budget_limit]

    return {
        "city": city.strip().title(),
        "budget": budget,
        "currency": "INR",
        "options": sorted(matching, key=lambda x: x["price_per_night"]),
        "total_available": len(all_hotels),
        "matching_count": len(matching),
    }
