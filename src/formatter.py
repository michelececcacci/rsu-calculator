"""Output formatting for RSU calculator results."""

from decimal import Decimal
from typing import List, Tuple

from src.calculator import LotResult
from src.currency import format_currency_amount


def format_lot_output(lot_result: LotResult, label: str) -> List[str]:
    """Format per-lot summary lines."""
    r = lot_result
    return [
        f"\nRSU Gains Calculator - {label} ({r.ticker})",
        "-" * 40,
        f"Buy date:        {r.date_bought}",
        f"Sell date:       {r.date_sold}",
        f"Units:           {r.units}",
        "",
        f"Buy price:       ${r.buy_price:,.2f} per share",
        f"Sell price:      ${r.sell_price:,.2f} per share",
        f"Cost basis:      ${r.cost_basis:,.2f}",
        f"Proceeds:        ${r.proceeds:,.2f}",
        f"Gain/loss:       ${r.gain:,.2f} ({r.gain_pct:+.2f}%)",
    ]


def format_totals_output(
    total_cost_basis: Decimal,
    total_proceeds: Decimal,
    total_gain: Decimal,
    total_gain_pct: Decimal,
) -> List[str]:
    """Format aggregate totals section."""
    return [
        f"\n{'=' * 40}",
        "TOTAL",
        "-" * 40,
        f"Cost basis:      ${total_cost_basis:,.2f}",
        f"Proceeds:        ${total_proceeds:,.2f}",
        f"Gain/loss:       ${total_gain:,.2f} ({total_gain_pct:+.2f}%)",
    ]


def format_fx_output(
    fx_gains: List[Tuple[str, Decimal]],
) -> List[str]:
    """Format FX gain section. Returns empty list if no FX data."""
    if not fx_gains:
        return []
    lines = [
        "\nGain/loss in other currencies "
        "(buy-date rate for cost basis, sell-date for proceeds):",
    ]
    for code, gain in fx_gains:
        lines.append(f"  {format_currency_amount(gain, code)}")
    return lines
