"""Gain/loss calculation logic."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, NamedTuple, Tuple

from src.rsu_lot import RSULot

TWO_PLACES = Decimal("0.01")


class LotResult(NamedTuple):
    """Result of calculating a single RSU lot."""

    ticker: str
    date_bought: str
    date_sold: str
    units: int
    buy_price: Decimal
    sell_price: Decimal
    cost_basis: Decimal
    proceeds: Decimal
    gain: Decimal
    gain_pct: Decimal
    date_bought_d: date
    date_sold_d: date


def compute_lot(
    lot: RSULot,
    buy_price: Decimal,
    sell_price: Decimal,
) -> LotResult:
    """
    Compute cost basis, proceeds, and gain for a single RSU lot.
    """
    cost_basis = (buy_price * lot.units).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )
    proceeds = (sell_price * lot.units).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )
    gain = proceeds - cost_basis
    gain_pct = (
        (gain / cost_basis * 100) if cost_basis else Decimal("0")
    ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    return LotResult(
        ticker=lot.ticker,
        date_bought=lot.date_bought,
        date_sold=lot.date_sold,
        units=lot.units,
        buy_price=buy_price,
        sell_price=sell_price,
        cost_basis=cost_basis,
        proceeds=proceeds,
        gain=gain,
        gain_pct=gain_pct,
        date_bought_d=date.fromisoformat(lot.date_bought),
        date_sold_d=date.fromisoformat(lot.date_sold),
    )


def compute_totals(
    lot_results: List[LotResult],
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Compute aggregate cost basis, proceeds, gain, and gain %.
    Returns (total_cost_basis, total_proceeds, total_gain, total_gain_pct).
    """
    total_cost_basis = sum(r.cost_basis for r in lot_results)
    total_proceeds = sum(r.proceeds for r in lot_results)
    total_gain = total_proceeds - total_cost_basis
    total_gain_pct = (
        (total_gain / total_cost_basis * 100) if total_cost_basis else Decimal("0")
    ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    return total_cost_basis, total_proceeds, total_gain, total_gain_pct
