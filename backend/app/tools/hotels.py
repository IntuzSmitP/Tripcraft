"""
Hotel availability integration layer.

Serves as the bridge between the agent's LLM interface and the underlying
headless web scraper (`fetch_hotel.py`). Handles parameter normalization,
date bounds checking, and response pagination to keep LLM context lightweight.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.tools.fetch_hotel import fetch_hotel_details


def search_hotels(
    city_name: str,
    checkin: str = "",
    checkout: str = "",
    adults: int = 1,
    rooms: int = 1,
    budget: float | None = None,
) -> dict[str, Any]:
    """
    Search for hotel options in a given city with check-in, check-out, adults, and rooms.

    Args:
        city_name: Destination city name (e.g. "Ahmedabad", "Goa").
        checkin: Check-in date in YYYY-MM-DD format (e.g. "2026-08-24").
        checkout: Check-out date in YYYY-MM-DD format (e.g. "2026-08-25").
        adults: Number of adult guests (default: 1).
        rooms: Number of rooms required (default: 1).
        budget: Maximum budget per night in INR (optional).

    Returns:
        Dict with city_name, checkin, checkout, adults, rooms, budget, currency,
        and list of hotels with real scraped fields (hotel_id, name, star_rating,
        guest_rating_score, guest_rating_label, review_count, location, price,
        display_price, currency, priced_check_in, priced_check_out, image).
    """
    # Handle positional budget argument for backward compatibility (e.g. search_hotels("Goa", 2000))
    if isinstance(checkin, (int, float)):
        budget = float(checkin)
        checkin = ""

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if not checkin or not isinstance(checkin, str) or checkin.isdigit():
        if isinstance(checkin, (int, float)) or (isinstance(checkin, str) and checkin.isdigit()):
            try:
                budget = float(checkin)
            except ValueError:
                pass
        checkin = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
    if not checkout or not isinstance(checkout, str):
        checkout = (today + timedelta(days=8)).strftime("%Y-%m-%d")

    # Parse and validate dates to prevent scraper crashing on past or inverted dates
    try:
        d1 = datetime.strptime(checkin, "%Y-%m-%d")
    except Exception:
        d1 = today + timedelta(days=7)
        
    try:
        d2 = datetime.strptime(checkout, "%Y-%m-%d")
    except Exception:
        d2 = d1 + timedelta(days=1)

    # Scraper cannot search for dates in the past
    if d1 < today:
        d1 = today + timedelta(days=7)
        
    # Checkout must be after checkin
    if d2 <= d1:
        d2 = d1 + timedelta(days=1)

    checkin = d1.strftime("%Y-%m-%d")
    checkout = d2.strftime("%Y-%m-%d")
    nights = (d2 - d1).days

    hotels = fetch_hotel_details(
        city_name=city_name,
        checkin=checkin,
        checkout=checkout,
        adults=int(adults) if adults else 1,
        rooms=int(rooms) if rooms else 1,
    )

    try:
        budget_limit = float(budget) if budget is not None else float("inf")
    except (ValueError, TypeError):
        budget_limit = float("inf")

    # Process scraped hotel pricing (scraper provides per-night price)
    processed_hotels = []
    for h in hotels:
        raw_price = float(h.get("price") or 0)
        
        # Skip sold-out hotels which have missing or 0 price
        if raw_price <= 0:
            continue
            
        # Scraper returns per-night price; multiply by nights to calculate total stay price
        per_night = raw_price
        total_stay_price = round(per_night * nights, 2) if nights > 0 else per_night
        item = dict(h)
        item["total_stay_price"] = total_stay_price
        item["price_per_night"] = per_night
        item["price"] = per_night  # Standardise price field to per-night price
        item["display_price_per_night"] = f"₹ {int(per_night):,}"
        item["rating"] = float(h.get("star_rating") or 4.0)
        item["type"] = "luxury" if (h.get("star_rating") or 0) >= 5 else ("mid-range" if (h.get("star_rating") or 0) >= 4 else "budget")
        processed_hotels.append(item)

    # Filter by per-night budget limit
    matching = [h for h in processed_hotels if h["price_per_night"] <= budget_limit]
    sorted_matching = sorted(matching, key=lambda x: x["price_per_night"])
    
    # Cap options to top 6 to keep LLM context light, fast, and within API timeout limits
    options_to_return = sorted_matching[:6]

    return {
        "city": city_name.strip().title(),
        "checkin": checkin,
        "checkout": checkout,
        "nights": nights,
        "adults": adults,
        "rooms": rooms,
        "budget": budget,
        "currency": "INR",
        "options": options_to_return,
        "total_available": len(hotels),
        "matching_count": len(options_to_return),
    }
