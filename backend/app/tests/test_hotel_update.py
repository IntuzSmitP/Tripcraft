"""
Tests for hotel selection & update API endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.routes.planning import _sessions
from app.models.state import AgentState
from app.models.plan import FinalOutput, HotelInfo, BudgetSummary, TripSummary

client = TestClient(app)
headers = {"Authorization": f"Bearer {settings.api_bearer_token}"}


def test_get_hotels_and_update_hotel():
    # Setup session mock
    state = AgentState(goal="3 day trip to Goa")
    session_id = state.id

    state.add_tool_result(
        "search_hotels",
        {"city_name": "Goa"},
        {
            "city": "Goa",
            "options": [
                {
                    "name": "Hotel AI Pick",
                    "price_per_night": 2000,
                    "rating": 4.5,
                    "type": "luxury",
                    "location": "North Goa"
                },
                {
                    "name": "Hotel Option B",
                    "price_per_night": 1200,
                    "rating": 4.0,
                    "type": "mid-range",
                    "location": "South Goa"
                }
            ]
        }
    )

    output = FinalOutput(
        trip=TripSummary(destination="Goa", duration_days=3, origin="Mumbai"),
        budget=BudgetSummary(requested=10000, estimated=6000, breakdown={"flights": 2000, "hotels": 4000}),
        hotel=HotelInfo(name="Hotel AI Pick", price_per_night=2000, total_price=4000, nights=2, rating=4.5),
        status="feasible"
    )

    _sessions[session_id] = {
        "state": state,
        "registry": None,
        "output": output,
        "done": True
    }

    # Test GET /api/plan/{session_id}/hotels
    res = client.get(f"/api/plan/{session_id}/hotels", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["hotels"]) == 2
    assert data["hotels"][0]["name"] == "Hotel AI Pick"
    assert data["hotels"][1]["name"] == "Hotel Option B"

    # Test PATCH /api/plan/{session_id}/hotel
    patch_res = client.patch(
        f"/api/plan/{session_id}/hotel",
        json={"hotel_name": "Hotel Option B"},
        headers=headers
    )
    assert patch_res.status_code == 200
    updated_plan = patch_res.json()
    assert updated_plan["hotel"]["name"] == "Hotel Option B"
    assert updated_plan["hotel"]["price_per_night"] == 1200
    assert updated_plan["hotel"]["total_price"] == 2400  # 1200 * 2 nights
    assert updated_plan["budget"]["breakdown"]["hotels"] == 2400
    assert updated_plan["budget"]["estimated"] == 4400  # 2000 flight + 2400 hotel


def test_multi_city_hotels():
    state = AgentState(goal="3 day trip to Kochi & Varkala")
    session_id = state.id

    state.add_tool_result(
        "search_hotels",
        {"city_name": "Kochi"},
        {
            "city": "Kochi",
            "options": [
                {"name": "Kochi Hotel 1", "price_per_night": 2500, "rating": 4.2},
                {"name": "Kochi Hotel 2", "price_per_night": 3200, "rating": 4.5}
            ]
        }
    )

    state.add_tool_result(
        "search_hotels",
        {"city_name": "Varkala"},
        {
            "city": "Varkala",
            "options": [
                {"name": "Varkala Resort", "price_per_night": 1800, "rating": 4.0}
            ]
        }
    )

    output = FinalOutput(
        trip=TripSummary(destination="Kochi & Varkala", duration_days=3),
        budget=BudgetSummary(requested=20000, estimated=8000, breakdown={"hotels": 5000}),
        hotel=HotelInfo(name="Kochi Hotel 1", price_per_night=2500, total_price=5000, nights=2),
        status="feasible"
    )

    _sessions[session_id] = {
        "state": state,
        "registry": None,
        "output": output,
        "done": True
    }

    # Test GET /api/plan/{session_id}/hotels
    res = client.get(f"/api/plan/{session_id}/hotels", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["hotels"]) == 3
    assert data["cities"] == ["Kochi", "Varkala"]
    assert "Kochi" in data["by_city"]
    assert "Varkala" in data["by_city"]
    assert len(data["by_city"]["Kochi"]) == 2
    assert len(data["by_city"]["Varkala"]) == 1

    # Test re-selecting hotel in Varkala
    patch_res = client.patch(
        f"/api/plan/{session_id}/hotel",
        json={"hotel_name": "Varkala Resort"},
        headers=headers
    )
    assert patch_res.status_code == 200
    updated_plan = patch_res.json()
    assert updated_plan["hotel"]["name"] == "Varkala Resort"
    assert updated_plan["hotel"]["city"] == "Varkala"
    assert updated_plan["hotel"]["price_per_night"] == 1800
