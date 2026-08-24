"""
Mock currency conversion tool.

Uses static exchange rates — no external API calls.
"""

from __future__ import annotations


_EXCHANGE_RATES: dict[str, dict[str, float]] = {
    "INR": {"USD": 0.012, "EUR": 0.011, "GBP": 0.0095, "INR": 1.0, "THB": 0.42, "AED": 0.044},
    "USD": {"INR": 83.50, "EUR": 0.92, "GBP": 0.79, "USD": 1.0, "THB": 35.0, "AED": 3.67},
    "EUR": {"INR": 90.50, "USD": 1.09, "GBP": 0.86, "EUR": 1.0, "THB": 38.0, "AED": 3.99},
    "GBP": {"INR": 105.50, "USD": 1.27, "EUR": 1.17, "GBP": 1.0, "THB": 44.5, "AED": 4.65},
}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Convert an amount from one currency to another.

    Args:
        amount: The amount of money to convert (e.g. 15000.0).
        from_currency: Source currency code, e.g. "INR".
        to_currency: Target currency code, e.g. "USD".

    Returns:
        A dict containing original amount, converted amount,
        exchange rate, and currency codes.
    """
    try:
        amount = float(amount)
    except ValueError:
        pass
    src = from_currency.strip().upper()
    dst = to_currency.strip().upper()

    if src not in _EXCHANGE_RATES:
        return {
            "error": f"Unsupported source currency: {src}",
            "supported": list(_EXCHANGE_RATES.keys()),
        }

    rates = _EXCHANGE_RATES[src]
    if dst not in rates:
        return {
            "error": f"Unsupported target currency: {dst}",
            "supported": list(rates.keys()),
        }

    rate = rates[dst]
    converted = round(amount * rate, 2)

    return {
        "from_currency": src,
        "to_currency": dst,
        "amount": amount,
        "converted_amount": converted,
        "exchange_rate": rate,
    }
