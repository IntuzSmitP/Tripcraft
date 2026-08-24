"""
Mock weather check tool.

Returns seasonal weather data based on city and month.
"""

from __future__ import annotations


# month-number → season → weather data
_WEATHER_PROFILES: dict[str, dict[str, dict]] = {
    "goa": {
        "summer": {"condition": "Hot & Humid", "temp_high": 35, "temp_low": 27, "humidity": 75, "recommendation": "Carry sunscreen and stay hydrated. Beach activities best in early morning or evening."},
        "monsoon": {"condition": "Heavy Rain", "temp_high": 30, "temp_low": 24, "humidity": 90, "recommendation": "Expect heavy rainfall. Many beach shacks close. Carry rain gear. Waterfalls are spectacular."},
        "winter": {"condition": "Pleasant & Warm", "temp_high": 32, "temp_low": 20, "humidity": 55, "recommendation": "Perfect weather for beaches and sightseeing. Peak tourist season."},
    },
    "mumbai": {
        "summer": {"condition": "Hot & Humid", "temp_high": 36, "temp_low": 26, "humidity": 70, "recommendation": "Very hot. Stay indoors during midday."},
        "monsoon": {"condition": "Heavy Rain", "temp_high": 30, "temp_low": 24, "humidity": 85, "recommendation": "Famous Mumbai monsoon. Carry umbrella at all times."},
        "winter": {"condition": "Mild & Pleasant", "temp_high": 32, "temp_low": 18, "humidity": 50, "recommendation": "Best time to visit. Comfortable weather."},
    },
    "delhi": {
        "summer": {"condition": "Extremely Hot", "temp_high": 45, "temp_low": 30, "humidity": 35, "recommendation": "Extreme heat. Avoid outdoor activities during afternoon."},
        "monsoon": {"condition": "Warm & Rainy", "temp_high": 35, "temp_low": 26, "humidity": 75, "recommendation": "Occasional heavy showers. Humidity is high."},
        "winter": {"condition": "Cold & Foggy", "temp_high": 20, "temp_low": 5, "humidity": 60, "recommendation": "Cold mornings. Carry warm clothing. Fog may affect travel."},
    },
    "jaipur": {
        "summer": {"condition": "Very Hot & Dry", "temp_high": 44, "temp_low": 28, "humidity": 25, "recommendation": "Scorching heat. Indoor sightseeing recommended."},
        "monsoon": {"condition": "Warm & Occasional Rain", "temp_high": 35, "temp_low": 25, "humidity": 65, "recommendation": "Moderate rain. Good time for fort visits."},
        "winter": {"condition": "Cool & Dry", "temp_high": 22, "temp_low": 8, "humidity": 40, "recommendation": "Ideal weather for sightseeing. Peak tourist season."},
    },
    "bangalore": {
        "summer": {"condition": "Warm & Pleasant", "temp_high": 36, "temp_low": 22, "humidity": 40, "recommendation": "Warm but manageable. Good for outdoor activities."},
        "monsoon": {"condition": "Moderate Rain", "temp_high": 28, "temp_low": 20, "humidity": 75, "recommendation": "Regular showers. Carry an umbrella."},
        "winter": {"condition": "Cool & Pleasant", "temp_high": 27, "temp_low": 15, "humidity": 45, "recommendation": "Very comfortable weather."},
    },
    "kolkata": {
        "summer": {"condition": "Hot & Humid", "temp_high": 38, "temp_low": 26, "humidity": 80, "recommendation": "Very humid. Stay hydrated."},
        "monsoon": {"condition": "Heavy Rain", "temp_high": 33, "temp_low": 26, "humidity": 90, "recommendation": "Heavy monsoon. Flooding possible. Plan accordingly."},
        "winter": {"condition": "Mild & Dry", "temp_high": 26, "temp_low": 12, "humidity": 50, "recommendation": "Best time to visit. Pleasant weather."},
    },
}

_DEFAULT_WEATHER = {
    "summer": {"condition": "Warm", "temp_high": 35, "temp_low": 25, "humidity": 60, "recommendation": "Check local weather before travel."},
    "monsoon": {"condition": "Rainy", "temp_high": 30, "temp_low": 23, "humidity": 80, "recommendation": "Carry rain gear."},
    "winter": {"condition": "Pleasant", "temp_high": 28, "temp_low": 15, "humidity": 50, "recommendation": "Comfortable for travel."},
}


def _get_season(month: int) -> str:
    """Map a month number to an Indian season."""
    if month in (3, 4, 5):
        return "summer"
    elif month in (6, 7, 8, 9):
        return "monsoon"
    else:
        return "winter"


def check_weather(city: str, date: str) -> dict:
    """
    Check the weather forecast for a city on a given date.

    Args:
        city: City name (e.g. "Goa").
        date: Date in YYYY-MM-DD format (e.g. "2026-09-10").

    Returns:
        A dict containing city, date, weather condition, temperature
        range, humidity percentage, and a travel recommendation.
    """
    key = city.strip().lower()

    # Parse month from date
    try:
        month = int(date.split("-")[1])
    except (IndexError, ValueError):
        month = 1  # fallback

    season = _get_season(month)
    profiles = _WEATHER_PROFILES.get(key, _DEFAULT_WEATHER)
    weather = profiles.get(season, profiles.get("winter", {}))

    return {
        "city": city.strip().title(),
        "date": date,
        "season": season,
        "condition": weather.get("condition", "Unknown"),
        "temperature_high_celsius": weather.get("temp_high"),
        "temperature_low_celsius": weather.get("temp_low"),
        "humidity_percent": weather.get("humidity"),
        "recommendation": weather.get("recommendation", ""),
    }
