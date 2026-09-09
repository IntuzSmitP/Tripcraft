"""
Client-facing exception sanitizer.

Intercepts raw system exceptions, network timeouts, and API provider faults,
translating them into safe, user-friendly messages. Prevents leaking stack traces
or sensitive infrastructure details to the frontend UI.
"""

from __future__ import annotations

import re


def friendly_error(raw: str | Exception) -> str:
    """Convert a raw exception or error string into a user-friendly message."""
    text = str(raw).lower()

    # Rate limiting / quota exhaustion
    if "resource_exhausted" in text or "429" in text or "rate" in text and "limit" in text:
        return (
            "Our AI service is temporarily busy due to high demand."
            "Please wait a moment and try again."
        )

    # Timeout / deadline
    if "deadline" in text or "timeout" in text or "504" in text:
        return (
            "The request took too long to process. "
            "Please try again — it usually works on the second attempt."
        )

    #Authentication / billing 
    if "401" in text or "403" in text or "unauthorized" in text:
        return "There's a configuration issue on our end. Please try again later."

    if "402" in text or "payment" in text or "billing" in text:
        return "There's a configuration issue on our end. Please try again later."

    #Model not found
    if "404" in text and ("model" in text or "not found" in text):
        return "There's a configuration issue on our end. Please try again later."

    # Network / connection errors
    if "connection" in text or "network" in text or "unreachable" in text:
        return (
            "Unable to reach the AI service. "
            "Please check your internet connection and try again."
        )

    # Server errors
    if "500" in text or "internal server error" in text:
        return "Something went wrong on our end. Please try again."

    if "503" in text or "unavailable" in text:
        return "The AI service is temporarily unavailable. Please try again shortly."

    # Generic fallback
    return "Something went wrong while planning your trip. Please try again."
