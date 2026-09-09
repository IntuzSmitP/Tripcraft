"""
Unit test suite for mocked tool integrations.

Validates parameter handling, edge cases, and JSON schema compliance for all
simulated external API dependencies (flights, hotels, currency, weather).
"""

import pytest

from app.tools.flights import search_flights
from app.tools.hotels import search_hotels
from app.tools.currency import convert_currency
from app.tools.weather import check_weather


# Flight Tests


class TestSearchFlights:
    def test_goa_returns_expensive_flights(self):
        """Goa flights are deliberately expensive for self-correction scenario."""
        result = search_flights("Ahmedabad", "Goa", "2026-09-10")

        assert result["origin"] == "Ahmedabad"
        assert result["destination"] == "Goa"
        assert result["date"] == "2026-09-10"
        assert len(result["options"]) >= 2
        # Cheapest Goa flight should be >= 8500 (self-correction trigger)
        cheapest = result["options"][0]["price"]
        assert cheapest >= 8500

    def test_mumbai_returns_affordable_flights(self):
        result = search_flights("Ahmedabad", "Mumbai", "2026-10-01")

        assert result["destination"] == "Mumbai"
        assert len(result["options"]) >= 1
        cheapest = result["options"][0]["price"]
        assert cheapest <= 5000

    def test_unknown_destination_returns_defaults(self):
        result = search_flights("Delhi", "Timbuktu", "2026-11-15")

        assert result["destination"] == "Timbuktu"
        assert len(result["options"]) >= 1

    def test_results_sorted_by_price(self):
        result = search_flights("Ahmedabad", "Goa", "2026-09-10")

        prices = [opt["price"] for opt in result["options"]]
        assert prices == sorted(prices)

    def test_case_insensitive_destination(self):
        result1 = search_flights("X", "GOA", "2026-01-01")
        result2 = search_flights("X", "goa", "2026-01-01")

        assert result1["options"] == result2["options"]

    def test_whitespace_handling(self):
        result = search_flights("  Ahmedabad  ", "  Goa  ", "2026-09-10")
        assert result["origin"] == "Ahmedabad"
        assert result["destination"] == "Goa"


# Hotel Tests


class TestSearchHotels:
    def test_goa_within_budget(self):
        result = search_hotels("Goa", 2000)

        assert result["city"] == "Goa"
        assert result["budget"] == 2000
        assert all(h["price_per_night"] <= 2000 for h in result["options"])

    def test_goa_low_budget_returns_hostels(self):
        result = search_hotels("Goa", 1000)

        assert len(result["options"]) >= 1
        assert result["options"][0]["price_per_night"] <= 1000

    def test_goa_very_low_budget_returns_empty(self):
        result = search_hotels("Goa", 1)

        assert len(result["options"]) == 0

    def test_unknown_city_returns_defaults(self):
        result = search_hotels("Timbuktu", 5000)

        assert "options" in result

    def test_results_sorted_by_price(self):
        result = search_hotels("Goa", 10000)

        prices = [h["price_per_night"] for h in result["options"]]
        assert prices == sorted(prices)

    def test_matching_count_correct(self):
        result = search_hotels("Goa", 2000)
        assert result["matching_count"] == len(result["options"])
        assert result["total_available"] >= result["matching_count"]


# Currency Tests


class TestConvertCurrency:
    def test_inr_to_usd(self):
        result = convert_currency(15000, "INR", "USD")

        assert result["from_currency"] == "INR"
        assert result["to_currency"] == "USD"
        assert result["amount"] == 15000
        assert result["converted_amount"] > 0
        assert result["exchange_rate"] > 0

    def test_identity_conversion(self):
        result = convert_currency(100, "INR", "INR")

        assert result["converted_amount"] == 100.0
        assert result["exchange_rate"] == 1.0

    def test_unsupported_source_currency(self):
        result = convert_currency(100, "XYZ", "USD")

        assert "error" in result
        assert "supported" in result

    def test_unsupported_target_currency(self):
        result = convert_currency(100, "INR", "XYZ")

        assert "error" in result

    def test_case_insensitive(self):
        result = convert_currency(100, "inr", "usd")

        assert result["from_currency"] == "INR"
        assert result["to_currency"] == "USD"


# Weather Tests


class TestCheckWeather:
    def test_goa_monsoon(self):
        result = check_weather("Goa", "2026-09-10")

        assert result["city"] == "Goa"
        assert result["season"] == "monsoon"
        assert "rain" in result["condition"].lower() or "humid" in result["condition"].lower()
        assert result["humidity_percent"] > 70

    def test_goa_winter(self):
        result = check_weather("Goa", "2026-12-15")

        assert result["season"] == "winter"
        assert result["temperature_high_celsius"] > 20

    def test_delhi_summer(self):
        result = check_weather("Delhi", "2026-04-15")

        assert result["season"] == "summer"
        assert result["temperature_high_celsius"] >= 40

    def test_unknown_city(self):
        result = check_weather("Timbuktu", "2026-06-15")

        assert result["city"] == "Timbuktu"
        assert "condition" in result

    def test_invalid_date_fallback(self):
        result = check_weather("Goa", "invalid-date")

        assert "condition" in result
        # Should fallback gracefully
