"""
Structured payload schemas for the final execution response.

These models define the strict API contract between the LLM's final 
planning output and the client interface, ensuring predictable parsing.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TransportInfo(BaseModel):
    mode: str = Field(default="flight")
    airline: str | None = None
    origin: str | None = None
    destination: str | None = None
    price: float | None = None
    currency: str = "INR"
    duration_hours: float | None = None
    date: str | None = None


class HotelInfo(BaseModel):
    name: str | None = None
    city: str | None = None
    price_per_night: float | None = None
    total_price: float | None = None
    nights: int | None = None
    rating: float | None = None
    currency: str = "INR"


class WeatherInfo(BaseModel):
    city: str | None = None
    date: str | None = None
    condition: str | None = None
    temperature_high: float | None = None
    temperature_low: float | None = None
    humidity: float | None = None
    recommendation: str | None = None


class BudgetSummary(BaseModel):
    requested: float | None = 0
    estimated: float | None = 0
    currency: str | None = "INR"
    breakdown: dict[str, float] | None = Field(default_factory=dict)


class TripSummary(BaseModel):
    destination: str | None = None
    duration_days: int | None = None
    date: str | None = None
    origin: str | None = None


class FinalOutput(BaseModel):
    """
    The structured JSON plan returned as the final response.
    Matches the spec exactly.
    """

    trip: TripSummary | dict[str, Any] | None = Field(default_factory=TripSummary)
    budget: BudgetSummary | dict[str, Any] | None = Field(default_factory=BudgetSummary)
    transport: TransportInfo | dict[str, Any] | None = Field(default_factory=dict)
    hotel: HotelInfo | dict[str, Any] | None = Field(default_factory=dict)
    hotels: list[HotelInfo] | list[dict[str, Any]] | None = Field(default_factory=list)
    weather: WeatherInfo | dict[str, Any] | None = Field(default_factory=dict)
    assumptions_changed: list[str] | None = Field(default_factory=list)
    status: str | None = Field(default="feasible", description="feasible | infeasible")
    reason: str | None = Field(default=None, description="Only set when status=infeasible")
    suggestions: list[str] | None = Field(default_factory=list)
    execution_summary: list[str] | None = Field(default_factory=list)
