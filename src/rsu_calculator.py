#!/usr/bin/env python3
"""
RSU Gains Calculator

Calculates gains/losses from Restricted Stock Units using historical prices
fetched via yfinance. Input: list of RSU lots (ticker, units, date bought, date sold).
Uses Decimal for all monetary calculations to avoid float precision issues.
"""

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import yfinance as yf

from src.rsu_lot import RSULot

# Quantize monetary values to 2 decimal places (cents)
TWO_PLACES = Decimal("0.01")

# Target currencies for gain/loss display: (code, yfinance ticker, True if USD is base)
# USD base (e.g. USDJPY): rate = JPY per 1 USD → multiply USD by rate
# USD quote (e.g. EURUSD): rate = USD per 1 EUR → divide USD by rate to get EUR
EXTRA_CURRENCIES: list[tuple[str, str, bool]] = [
    ("EUR", "EURUSD=X", False),   # 1 EUR = X USD
    ("GBP", "GBPUSD=X", False),   # 1 GBP = X USD
    ("CHF", "USDCHF=X", True),    # 1 USD = X CHF
    ("JPY", "USDJPY=X", True),    # 1 USD = X JPY
]

# --- Input: edit this list ---
RSU_LOTS: list[RSULot] = [
    RSULot(ticker="AAPL", units=100, date_bought="2023-01-15", date_sold="2024-03-01"),
]


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD.")


def get_price_for_date(ticker: yf.Ticker, d: date) -> Optional[Decimal]:
    """
    Fetch adjusted close price for a single date.
    Assumes the market is open on the transaction date.
    Returns Decimal for precise monetary use; None if no data.
    """
    start = d.strftime("%Y-%m-%d")
    end = (datetime.combine(d, datetime.min.time()) + timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    hist = ticker.history(start=start, end=end, auto_adjust=True)

    if hist.empty:
        return None

    price_col = "Close" if "Close" in hist.columns else "Adj Close"
    val = hist[price_col].iloc[0]
    if val != val:  # NaN check
        return None
    # Use str() to avoid float→Decimal precision issues
    return Decimal(str(float(val))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def get_usd_to_currency_rate_for_date(ticker_symbol: str, d: date) -> Optional[Decimal]:
    """
    Fetch USD-to-foreign rate for a specific date from yfinance.
    For XXXUSD pairs (USD quote): returns USD per 1 XXX → divide usd_amount by rate.
    For USDXXX pairs (USD base): returns XXX per 1 USD → multiply usd_amount by rate.
    Uses nearest available rate if exact date has no data (e.g. weekends).
    """
    t = yf.Ticker(ticker_symbol)
    start = (datetime.combine(d, datetime.min.time()) - timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    end = (datetime.combine(d, datetime.min.time()) + timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    hist = t.history(start=start, end=end, auto_adjust=True)
    if hist.empty:
        return None
    price_col = "Close" if "Close" in hist.columns else "Adj Close"
    # Use last row (most recent on or before date; forex may be closed weekends)
    val = hist[price_col].iloc[-1]
    if val != val or val <= 0:  # NaN or invalid
        return None
    return Decimal(str(float(val))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def usd_to_currency(usd_amount: Decimal, rate: Decimal, usd_is_base: bool) -> Decimal:
    """Convert USD amount to foreign currency using the given rate."""
    if usd_is_base:
        return (usd_amount * rate).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    return (usd_amount / rate).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def format_currency_amount(amount: Decimal, code: str) -> str:
    """Format amount with appropriate decimals (0 for JPY, 2 for most others)."""
    decimals = 0 if code == "JPY" else 2
    return f"{amount:,.{decimals}f} {code}"


def main() -> int:
    if not RSU_LOTS:
        print("Error: No RSU lots to process.", file=sys.stderr)
        return 1

    total_cost_basis = Decimal("0")
    total_proceeds = Decimal("0")
    lot_results: list[tuple[Decimal, Decimal, date, date]] = []

    for i, lot in enumerate(RSU_LOTS):
        # Validate dates
        try:
            date_bought = parse_date(lot.date_bought)
            date_sold = parse_date(lot.date_sold)
        except ValueError as e:
            print(f"Error (lot {i + 1}): {e}", file=sys.stderr)
            return 1

        if date_bought >= date_sold:
            print(
                f"Error (lot {i + 1}): Buy date must be before sell date.",
                file=sys.stderr,
            )
            return 1

        if lot.units <= 0:
            print(
                f"Error (lot {i + 1}): Units must be positive.",
                file=sys.stderr,
            )
            return 1

        # Fetch prices
        t = yf.Ticker(lot.ticker)
        buy_price = get_price_for_date(t, date_bought.date())
        sell_price = get_price_for_date(t, date_sold.date())

        if buy_price is None:
            print(
                f"Error (lot {i + 1}): No price data for {lot.ticker} on or near "
                f"{lot.date_bought}. Check ticker symbol and date.",
                file=sys.stderr,
            )
            return 1

        if sell_price is None:
            print(
                f"Error (lot {i + 1}): No price data for {lot.ticker} on or near "
                f"{lot.date_sold}. Check ticker symbol and date.",
                file=sys.stderr,
            )
            return 1

        # Calculate gains (Decimal throughout for precision)
        cost_basis = (buy_price * lot.units).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        proceeds = (sell_price * lot.units).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        gain = proceeds - cost_basis
        gain_pct = (gain / cost_basis * 100) if cost_basis else Decimal("0")

        total_cost_basis += cost_basis
        total_proceeds += proceeds
        lot_results.append(
            (cost_basis, proceeds, date_bought.date(), date_sold.date())
        )

        # Print per-lot summary
        label = f"Lot {i + 1}" if len(RSU_LOTS) > 1 else lot.ticker
        print(f"\nRSU Gains Calculator - {label} ({lot.ticker})")
        print("-" * 40)
        print(f"Buy date:        {lot.date_bought}")
        print(f"Sell date:       {lot.date_sold}")
        print(f"Units:           {lot.units}")
        print()
        print(f"Buy price:       ${buy_price:,.2f} per share")
        print(f"Sell price:      ${sell_price:,.2f} per share")
        print(f"Cost basis:      ${cost_basis:,.2f}")
        print(f"Proceeds:        ${proceeds:,.2f}")
        print(f"Gain/loss:       ${gain:,.2f} ({gain_pct:+.2f}%)")

    # Print totals when multiple lots
    if len(RSU_LOTS) > 1:
        total_gain = total_proceeds - total_cost_basis
        total_gain_pct = (
            (total_gain / total_cost_basis * 100) if total_cost_basis else Decimal("0")
        )
        print(f"\n{'=' * 40}")
        print("TOTAL")
        print("-" * 40)
        print(f"Cost basis:      ${total_cost_basis:,.2f}")
        print(f"Proceeds:        ${total_proceeds:,.2f}")
        print(f"Gain/loss:       ${total_gain:,.2f} ({total_gain_pct:+.2f}%)")

    # Final gain (single lot or total) - show in other currencies
    # Cost basis uses buy-date rate; proceeds use sell-date rate
    if EXTRA_CURRENCIES:
        print(f"\nGain/loss in other currencies (buy-date rate for cost basis, sell-date for proceeds):")
        for code, ticker, usd_is_base in EXTRA_CURRENCIES:
            total_cost_basis_fx = Decimal("0")
            total_proceeds_fx = Decimal("0")
            ok = True
            for cost_basis, proceeds, date_bought_d, date_sold_d in lot_results:
                rate_buy = get_usd_to_currency_rate_for_date(ticker, date_bought_d)
                rate_sell = get_usd_to_currency_rate_for_date(ticker, date_sold_d)
                if rate_buy is None or rate_sell is None:
                    ok = False
                    break
                total_cost_basis_fx += usd_to_currency(cost_basis, rate_buy, usd_is_base)
                total_proceeds_fx += usd_to_currency(proceeds, rate_sell, usd_is_base)
            if ok:
                gain_fx = total_proceeds_fx - total_cost_basis_fx
                print(f"  {format_currency_amount(gain_fx, code)}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
