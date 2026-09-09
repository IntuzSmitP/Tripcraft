"""
Security and input validation hardening suite.

Subject endpoints to adversarial, oversized, and structurally invalid payloads.
Verifies the application boundary correctly sanitizes inputs and degrades 
gracefully via standard HTTP 4xx semantics without triggering internal 500 faults.

Usage:
    uv run pytest app/tests/test_api_hardening.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_TOKEN = "tripcraft-dev-token"
AUTH = {"Authorization": f"Bearer {VALID_TOKEN}"}


# Auth tests


class TestAuth:
    """Attacker tries to bypass authentication."""

    def test_no_auth_header(self):
        r = client.post("/api/plan", json={"goal": "Trip to Goa"})
        assert r.status_code in (401, 403)  # FastAPI returns 401 or 403 for missing Bearer

    def test_wrong_token(self):
        r = client.post(
            "/api/plan",
            json={"goal": "Trip to Goa 3 days"},
            headers={"Authorization": "Bearer wrong-token-12345"},
        )
        assert r.status_code == 401

    def test_empty_bearer(self):
        r = client.post(
            "/api/plan",
            json={"goal": "Trip to Goa 3 days"},
            headers={"Authorization": "Bearer "},
        )
        assert r.status_code in (401, 403)

    def test_no_bearer_prefix(self):
        r = client.post(
            "/api/plan",
            json={"goal": "Trip to Goa 3 days"},
            headers={"Authorization": VALID_TOKEN},
        )
        assert r.status_code in (401, 403)


# POST /api/plan — Goal validation


class TestPlanGoalValidation:
    """Attacker sends malformed goal payloads."""

    def test_empty_body(self):
        r = client.post("/api/plan", headers=AUTH)
        assert r.status_code == 422

    def test_no_goal_field(self):
        r = client.post("/api/plan", json={}, headers=AUTH)
        assert r.status_code == 422

    def test_goal_too_short(self):
        r = client.post("/api/plan", json={"goal": "hi"}, headers=AUTH)
        assert r.status_code == 422

    def test_goal_too_long(self):
        r = client.post("/api/plan", json={"goal": "x" * 501}, headers=AUTH)
        assert r.status_code == 422

    def test_goal_is_number(self):
        r = client.post("/api/plan", json={"goal": 12345}, headers=AUTH)
        assert r.status_code == 422

    def test_goal_is_null(self):
        r = client.post("/api/plan", json={"goal": None}, headers=AUTH)
        assert r.status_code == 422

    def test_goal_is_list(self):
        r = client.post("/api/plan", json={"goal": ["trip", "to", "goa"]}, headers=AUTH)
        assert r.status_code == 422

    def test_goal_is_nested_object(self):
        r = client.post("/api/plan", json={"goal": {"text": "trip to goa"}}, headers=AUTH)
        assert r.status_code == 422

    def test_extra_fields_ignored(self):
        """Extra fields should be silently ignored, not crash."""
        r = client.post(
            "/api/plan",
            json={"goal": "Plan a trip to Goa from Ahmedabad", "evil": "payload", "nested": {"a": 1}},
            headers=AUTH,
        )
        # Should succeed (extra fields are ignored by Pydantic)
        assert r.status_code == 200

    def test_invalid_json_body(self):
        r = client.post(
            "/api/plan",
            content="this is not json at all",
            headers={**AUTH, "Content-Type": "application/json"},
        )
        assert r.status_code == 422

    def test_html_injection_in_goal(self):
        """Goal with HTML/script tags should not crash."""
        r = client.post(
            "/api/plan",
            json={"goal": '<script>alert("xss")</script> plan trip to goa'},
            headers=AUTH,
        )
        # Should either succeed (200) or validate out (422), never 500
        assert r.status_code in (200, 422)

    def test_sql_injection_in_goal(self):
        r = client.post(
            "/api/plan",
            json={"goal": "Plan trip to Goa'; DROP TABLE users; --"},
            headers=AUTH,
        )
        assert r.status_code in (200, 422)

    def test_unicode_goal(self):
        r = client.post(
            "/api/plan",
            json={"goal": "गोवा में 3 दिन की ट्रिप प्लान करो 🏖️🌊"},
            headers=AUTH,
        )
        assert r.status_code == 200

    def test_emoji_only_goal(self):
        r = client.post(
            "/api/plan",
            json={"goal": "🏖️ 🌊 ✈️ 🏨 🍛"},
            headers=AUTH,
        )
        assert r.status_code == 200


# Session ID validation


class TestSessionIdValidation:
    """Attacker sends fake or malformed session IDs."""

    def test_nonexistent_session_stream(self):
        r = client.get("/api/plan/fakesession123/stream", headers=AUTH)
        assert r.status_code == 404

    def test_nonexistent_session_state(self):
        r = client.get("/api/plan/fakesession123/state", headers=AUTH)
        assert r.status_code == 404

    def test_nonexistent_session_result(self):
        r = client.get("/api/plan/fakesession123/result", headers=AUTH)
        assert r.status_code == 404

    def test_nonexistent_session_input(self):
        r = client.post(
            "/api/plan/fakesession123/input",
            json={"input": "test"},
            headers=AUTH,
        )
        assert r.status_code == 404

    def test_extremely_long_session_id(self):
        long_id = "a" * 100
        r = client.get(f"/api/plan/{long_id}/state", headers=AUTH)
        assert r.status_code == 422  # Path validation rejects > 50 chars

    def test_special_chars_session_id(self):
        r = client.get("/api/plan/../../etc/passwd/state", headers=AUTH)
        # Should be 404 (not found) — FastAPI routes don't allow path traversal
        assert r.status_code in (404, 422)

    def test_sql_injection_session_id(self):
        r = client.get("/api/plan/1' OR '1'='1/state", headers=AUTH)
        assert r.status_code in (404, 422)


# POST /api/plan/{id}/input — User input validation


class TestUserInputValidation:
    """Attacker sends malformed user input payloads."""

    def test_empty_input(self):
        r = client.post(
            "/api/plan/fakesession123/input",
            json={"input": ""},
            headers=AUTH,
        )
        assert r.status_code == 422  # min_length=1

    def test_input_too_long(self):
        r = client.post(
            "/api/plan/fakesession123/input",
            json={"input": "x" * 501},
            headers=AUTH,
        )
        assert r.status_code == 422  # max_length=500

    def test_no_input_field(self):
        r = client.post(
            "/api/plan/fakesession123/input",
            json={},
            headers=AUTH,
        )
        assert r.status_code == 422

    def test_input_is_number(self):
        r = client.post(
            "/api/plan/fakesession123/input",
            json={"input": 42},
            headers=AUTH,
        )
        assert r.status_code == 422

    def test_input_is_null(self):
        r = client.post(
            "/api/plan/fakesession123/input",
            json={"input": None},
            headers=AUTH,
        )
        assert r.status_code == 422


# Tool edge cases (direct function calls)


class TestToolEdgeCases:
    """Direct tool function calls with bad arguments."""

    def test_flights_empty_strings(self):
        from app.tools.flights import search_flights
        result = search_flights("", "", "")
        assert "options" in result

    def test_weather_empty_strings(self):
        from app.tools.weather import check_weather
        result = check_weather("", "")
        assert "condition" in result

    def test_currency_string_amount(self):
        from app.tools.currency import convert_currency
        result = convert_currency("15000", "INR", "USD")
        assert result["converted_amount"] > 0

    def test_currency_negative_amount(self):
        from app.tools.currency import convert_currency
        result = convert_currency(-100, "INR", "USD")
        assert "converted_amount" in result

    def test_currency_zero_amount(self):
        from app.tools.currency import convert_currency
        result = convert_currency(0, "INR", "USD")
        assert result["converted_amount"] == 0

    def test_currency_empty_currency_codes(self):
        from app.tools.currency import convert_currency
        result = convert_currency(100, "", "")
        assert "error" in result


# Health check


class TestHealthCheck:
    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["service"] == "TripCraft"

    def test_health_no_auth_required(self):
        """Health check should work without auth."""
        r = client.get("/health")
        assert r.status_code == 200
