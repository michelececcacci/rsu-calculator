"""Currency conversion and formatting."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

from src.price_fetcher import get_usd_to_currency_rate_for_date

TWO_PLACES = Decimal("0.01")

# Target currencies for gain/loss display: (code, yfinance ticker, True if USD is base)
# USD base (e.g. USDJPY): rate = JPY per 1 USD → multiply USD by rate
# USD quote (e.g. EURUSD): rate = USD per 1 EUR → divide USD by rate to get EUR
EXTRA_CURRENCIES: List[Tuple[str, str, bool]] = [
    ("EUR", "EURUSD=X", False),  # 1 EUR = X USD
    ("GBP", "GBPUSD=X", False),  # 1 GBP = X USD
    ("CHF", "USDCHF=X", True),   # 1 USD = X CHF
    ("JPY", "USDJPY=X", True),   # 1 USD = X JPY
]


def usd_to_currency(
    usd_amount: Decimal,
    rate: Decimal,
    usd_is_base: bool,
) -> Decimal:
    """Convert USD amount to foreign currency using the given rate."""
    if usd_is_base:
        return (usd_amount * rate).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    return (usd_amount / rate).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def format_currency_amount(amount: Decimal, code: str) -> str:
    """Format amount with appropriate decimals (0 for JPY, 2 for most others)."""
    decimals = 0 if code == "JPY" else 2
    return f"{amount:,.{decimals}f} {code}"


def get_fx_gains_for_lots(
    lot_results: List[Tuple[Decimal, Decimal, date, date]],
) -> List[Tuple[str, Decimal]]:
    """
    Compute gain in each extra currency for the given lot results.
    Returns list of (currency_code, gain_amount) for currencies where data was available.
    Skips currencies with missing FX data (no error raised).
    """
    results: List[Tuple[str, Decimal]] = []
    for code, ticker_symbol, usd_is_base in EXTRA_CURRENCIES:
        total_cost_basis_fx = Decimal("0")
        total_proceeds_fx = Decimal("0")
        ok = True
        for cost_basis, proceeds, date_bought_d, date_sold_d in lot_results:
            rate_buy = get_usd_to_currency_rate_for_date(ticker_symbol, date_bought_d)
            rate_sell = get_usd_to_currency_rate_for_date(ticker_symbol, date_sold_d)
            if rate_buy is None or rate_sell is None:
                ok = False
                break
            total_cost_basis_fx += usd_to_currency(
                cost_basis, rate_buy, usd_is_base
            )
            total_proceeds_fx += usd_to_currency(
                proceeds, rate_sell, usd_is_base
            )
        if ok:
            gain_fx = total_proceeds_fx - total_cost_basis_fx
            results.append((code, gain_fx))
    return results
