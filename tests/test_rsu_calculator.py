"""Tests for get_price_for_date.

Assumes market is open on transaction date. Function fetches single-day data
and returns price for that date or None.
"""

import unittest
from datetime import date
from decimal import Decimal
from typing import List, Tuple
from unittest.mock import MagicMock

import pandas as pd

from src.price_fetcher import get_price_for_date


def make_hist(dates_and_prices: List[Tuple[date, float]]) -> pd.DataFrame:
    """Build a history DataFrame from (date, price) pairs."""
    dates = pd.DatetimeIndex([pd.Timestamp(d) for d, _ in dates_and_prices])
    prices = [p for _, p in dates_and_prices]
    return pd.DataFrame({"Close": prices}, index=dates)


class TestGetPriceForDate(unittest.TestCase):
    def test_trading_day_returns_price(self) -> None:
        """When the date is a trading day, return that day's price."""
        ticker = MagicMock()
        ticker.history.return_value = make_hist([(date(2024, 1, 15), 105.0)])
        result = get_price_for_date(ticker, date(2024, 1, 15))
        self.assertEqual(result, Decimal("105.00"))

    def test_empty_history_returns_none(self) -> None:
        """When no data is returned (e.g. weekend/holiday), return None."""
        ticker = MagicMock()
        ticker.history.return_value = pd.DataFrame()
        result = get_price_for_date(ticker, date(2024, 1, 15))
        self.assertIsNone(result)

    def test_nan_price_returns_none(self) -> None:
        """When the price is NaN, return None."""
        ticker = MagicMock()
        df = pd.DataFrame(
            {"Close": [float("nan")]},
            index=pd.DatetimeIndex([pd.Timestamp("2024-01-15")]),
        )
        ticker.history.return_value = df
        result = get_price_for_date(ticker, date(2024, 1, 15))
        self.assertIsNone(result)

    def test_adj_close_fallback(self) -> None:
        """Use Adj Close when Close column is not present (older yfinance)."""
        ticker = MagicMock()
        df = pd.DataFrame(
            {"Adj Close": [99.5]},
            index=pd.DatetimeIndex([pd.Timestamp("2024-01-15")]),
        )
        ticker.history.return_value = df
        result = get_price_for_date(ticker, date(2024, 1, 15))
        self.assertEqual(result, Decimal("99.50"))


if __name__ == "__main__":
    unittest.main()
