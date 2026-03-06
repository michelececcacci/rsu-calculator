#!/usr/bin/env python3
"""
RSU Gains Calculator

Calculates gains/losses from Restricted Stock Units using historical prices
fetched via yfinance. Input: list of RSU lots (ticker, units, date bought, date sold).
Uses Decimal for all monetary calculations to avoid float precision issues.
"""

import sys
from typing import List, Optional

from src.calculator import LotResult, compute_lot, compute_totals
from src.currency import get_fx_gains_for_lots
from src.exceptions import (
    NetworkError,
    PriceDataError,
    RSUCalculatorError,
    ValidationError,
)
from src.formatter import format_fx_output, format_lot_output, format_totals_output
from src.price_fetcher import fetch_price_for_date
from src.rsu_lot import RSULot
from src.validation import validate_lot

# --- Input: edit this list ---
RSU_LOTS: List[RSULot] = [
    RSULot(ticker="AAPL", units=100, date_bought="2023-01-15", date_sold="2024-03-01"),
]


def _lot_results_for_fx(lot_results: List[LotResult]) -> list:
    """Build list of (cost_basis, proceeds, date_bought, date_sold) for FX conversion."""
    return [
        (r.cost_basis, r.proceeds, r.date_bought_d, r.date_sold_d)
        for r in lot_results
    ]


def _run(rsu_lots: List[RSULot]) -> int:
    """
    Run the calculator on the given RSU lots.
    Returns 0 on success, 1 on error. Prints to stdout/stderr.
    """
    if not rsu_lots:
        print("Error: No RSU lots to process.", file=sys.stderr)
        return 1

    lot_results: List[LotResult] = []

    for i, lot in enumerate(rsu_lots):
        try:
            date_bought, date_sold = validate_lot(lot, i)
        except ValidationError as e:
            _print_lot_error(i, str(e))
            return 1

        try:
            buy_price = fetch_price_for_date(
                lot.ticker,
                date_bought.date(),
                lot_index=i,
                date_label=lot.date_bought,
            )
            sell_price = fetch_price_for_date(
                lot.ticker,
                date_sold.date(),
                lot_index=i,
                date_label=lot.date_sold,
            )
        except PriceDataError as e:
            _print_lot_error(i, str(e))
            return 1
        except NetworkError as e:
            print(f"Error: {e}", file=sys.stderr)
            if e.cause:
                print(f"  Cause: {e.cause}", file=sys.stderr)
            return 1

        lot_result = compute_lot(lot, buy_price, sell_price)
        lot_results.append(lot_result)

        label = f"Lot {i + 1}" if len(rsu_lots) > 1 else lot.ticker
        for line in format_lot_output(lot_result, label):
            print(line)

    if len(rsu_lots) > 1:
        total_cost_basis, total_proceeds, total_gain, total_gain_pct = compute_totals(
            lot_results
        )
        for line in format_totals_output(
            total_cost_basis, total_proceeds, total_gain, total_gain_pct
        ):
            print(line)

    fx_data = get_fx_gains_for_lots(_lot_results_for_fx(lot_results))
    for line in format_fx_output(fx_data):
        print(line)

    print()
    return 0


def _print_lot_error(lot_index: int, message: str) -> None:
    """Print a lot-specific error to stderr."""
    print(f"Error (lot {lot_index + 1}): {message}", file=sys.stderr)


def main(rsu_lots: Optional[List[RSULot]] = None) -> int:
    """
    Main entry point. Runs calculator on RSU_LOTS (or provided list).
    Returns 0 on success, 1 on error. Handles all RSUCalculatorError subclasses.
    """
    lots = rsu_lots if rsu_lots is not None else RSU_LOTS
    try:
        return _run(lots)
    except RSUCalculatorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    sys.exit(main())
