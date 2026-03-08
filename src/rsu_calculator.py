import argparse
import sys
from typing import Callable, Optional, TypedDict

import pandas as pd

from src.fx_rate_calculator import FxRateCalculator
from src.models import Transaction, TransactionAction
from src.price_fetcher import PriceFetcher
from src.schwab_json_parser import SchwabJsonParser


class MatchedTransaction(TypedDict):
    Ticker: str
    Vest_Date: str  # noqa: N815
    Sell_Date: Optional[str]  # noqa: N815
    Shares: int


class RSUResult(TypedDict):
    Ticker: str
    Shares: int
    Vest_Date: str  # noqa: N815
    Sell_Date: str  # noqa: N815
    Vest_Price_USD: float  # noqa: N815
    Sell_Price_USD: float  # noqa: N815
    Cost_Basis_USD: float  # noqa: N815
    Proceeds_USD: float  # noqa: N815
    Gain_USD: float  # noqa: N815
    Cost_Basis_EUR: float  # noqa: N815
    Proceeds_EUR: float  # noqa: N815
    Gain_EUR: float  # noqa: N815


# Type aliases for injectable fetchers
PriceFetcherFn = Callable[[str, Optional[str]], Optional[float]]
RateFetcherFn = Callable[..., Optional[float]]


def match_transactions(transactions: list[Transaction]) -> list[MatchedTransaction]:
    vests = []
    sells = []

    for tx in transactions:
        date_str = tx.date.strftime("%Y-%m-%d")
        if tx.action == TransactionAction.VEST:
            vests.append(
                {"Date": date_str, "Quantity": tx.quantity, "Symbol": tx.symbol, "Matched": 0}
            )
        elif tx.action == TransactionAction.SELL:
            sells.append(
                {"Date": date_str, "Quantity": tx.quantity, "Symbol": tx.symbol, "Matched": 0}
            )

    # Sort by date
    vests.sort(key=lambda x: x["Date"])
    sells.sort(key=lambda x: x["Date"])

    data = []
    for vest in vests:
        vest_qty = vest["Quantity"]
        vest_sym = vest["Symbol"]
        vest_date = vest["Date"]

        remaining_vest = vest_qty
        for sell in sells:
            if (
                sell["Symbol"] == vest_sym
                and sell["Quantity"] - sell["Matched"] > 0
                and sell["Date"] >= vest_date
            ):
                available_sell = sell["Quantity"] - sell["Matched"]
                match_qty = min(remaining_vest, available_sell)
                sell["Matched"] += match_qty
                remaining_vest -= match_qty

                data.append(
                    {
                        "Ticker": vest_sym,
                        "Vest Date": vest_date,
                        "Sell Date": sell["Date"],
                        "Shares": match_qty,
                    }
                )
                if remaining_vest <= 0:
                    break

        if remaining_vest > 0:
            data.append(
                {
                    "Ticker": vest_sym,
                    "Vest Date": vest_date,
                    "Sell Date": None,
                    "Shares": remaining_vest,
                }
            )

    return data


_FX_CALCULATOR = None


def _get_fx_calculator() -> FxRateCalculator:
    """Return a lazily constructed shared FxRateCalculator instance."""
    global _FX_CALCULATOR
    if _FX_CALCULATOR is None:
        _FX_CALCULATOR = FxRateCalculator()
    return _FX_CALCULATOR


def get_exchange_rate(date_str: str, base_currency: str, target_currency: str) -> float:
    """Return the USD→EUR FX rate for the given date using ECB data.

    The `base_currency` and `target_currency` parameters are accepted for
    compatibility with injected/mocked implementations but are currently
    restricted to EUR/USD.
    """
    if base_currency != "EUR" or target_currency != "USD":
        raise ValueError("Only EUR/USD FX rates are supported.")

    fx = _get_fx_calculator()
    # ECB data is EUR→USD; invert to get USD→EUR so downstream code can
    # multiply USD amounts by this factor to obtain EUR values.
    eur_to_usd = fx.get_rate("USD", date_str)
    return 1.0 / float(eur_to_usd)


def calculate_rsu_metrics(
    data: list[MatchedTransaction],
    price_fetcher: Optional[PriceFetcherFn] = None,
    rate_fetcher: Optional[RateFetcherFn] = None,
) -> list[RSUResult]:
    if price_fetcher is None:
        price_fetcher = PriceFetcher.get_historical_price
    if rate_fetcher is None:
        rate_fetcher = get_exchange_rate

    results: list[RSUResult] = []
    for row in data:
        ticker: str = row["Ticker"]
        shares: int = row["Shares"]
        vest_date: str = row["Vest Date"]
        sell_date: Optional[str] = row["Sell Date"]

        # Prices
        vest_price_usd = price_fetcher(ticker, vest_date)
        sell_price_usd = price_fetcher(ticker, sell_date) if sell_date else None

        # Forex: factor to convert USD amounts into EUR using ECB FX data
        usd_to_eur_vest = rate_fetcher(vest_date, base_currency="EUR", target_currency="USD")
        usd_to_eur_sell = (
            rate_fetcher(sell_date, base_currency="EUR", target_currency="USD")
            if sell_date
            else None
        )

        # Calculations
        cost_basis_usd = shares * vest_price_usd
        cost_basis_eur = cost_basis_usd * usd_to_eur_vest

        proceeds_usd = None
        proceeds_eur = None
        gain_eur = None
        gain_usd = None

        if sell_date and sell_price_usd and usd_to_eur_sell is not None:
            proceeds_usd = shares * sell_price_usd
            proceeds_eur = proceeds_usd * usd_to_eur_sell
            gain_usd = proceeds_usd - cost_basis_usd
            gain_eur = proceeds_eur - cost_basis_eur

        results.append(
            {
                "Ticker": ticker,
                "Shares": shares,
                "Vest Date": vest_date,
                "Sell Date": sell_date or "N/A",
                "Vest Price (USD)": round(vest_price_usd, 2),
                "Sell Price (USD)": round(sell_price_usd, 2) if sell_price_usd else 0.0,
                "Cost Basis (USD)": round(cost_basis_usd, 2),
                "Proceeds (USD)": round(proceeds_usd, 2) if proceeds_usd is not None else 0.0,
                "Gain (USD)": round(gain_usd, 2) if gain_usd is not None else 0.0,
                "Cost Basis (EUR)": round(cost_basis_eur, 2),
                "Proceeds (EUR)": round(proceeds_eur, 2) if proceeds_eur is not None else 0.0,
                "Gain (EUR)": round(gain_eur, 2) if gain_eur is not None else 0.0,
            }
        )

    return results


def print_summary(results: list[RSUResult]) -> None:
    df = pd.DataFrame(results)

    display_cols = [
        "Ticker",
        "Shares",
        "Vest Date",
        "Sell Date",
        "Vest Price (USD)",
        "Sell Price (USD)",
        "Cost Basis (EUR)",
        "Proceeds (EUR)",
        "Gain (EUR)",
    ]
    print("\n--- RSU Summary ---")
    print(df[display_cols].to_string(index=False))

    print("\n--- Totals ---")
    total_cost_eur = df["Cost Basis (EUR)"].sum()
    total_proceeds_eur = df["Proceeds (EUR)"].sum()
    total_gain_eur = df["Gain (EUR)"].sum()
    total_proceeds_usd = df["Proceeds (USD)"].sum()
    total_gain_usd = df["Gain (USD)"].sum()

    print(f"Total Cost Basis (EUR): {total_cost_eur:,.2f}")
    if any(r["Sell Date"] != "N/A" for r in results):
        print(f"Total Proceeds (EUR)  : {total_proceeds_eur:,.2f}")
        print(f"Total Gain (EUR)      : {total_gain_eur:,.2f}")
        print(f"Total Proceeds (USD)  : {total_proceeds_usd:,.2f}")
        print(f"Total Gain (USD)      : {total_gain_usd:,.2f}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate Cost Basis and Gains for RSUs in EUR.")
    parser.add_argument("file", help="Path to the input CSV or JSON file")
    args = parser.parse_args()

    try:
        transactions = SchwabJsonParser.parse_file(args.file)
        data = match_transactions(transactions)
        results = calculate_rsu_metrics(data)
        print_summary(results)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
