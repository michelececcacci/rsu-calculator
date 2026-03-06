"""Tests for validation module."""

import unittest
from datetime import datetime

from src.exceptions import ValidationError
from src.rsu_lot import RSULot
from src.validation import parse_date, validate_lot


class TestParseDate(unittest.TestCase):
    def test_valid_date(self) -> None:
        result = parse_date("2024-01-15")
        self.assertEqual(result, datetime(2024, 1, 15))

    def test_strips_whitespace(self) -> None:
        result = parse_date("  2024-01-15  ")
        self.assertEqual(result, datetime(2024, 1, 15))

    def test_invalid_format_raises(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            parse_date("01/15/2024")
        self.assertIn("YYYY-MM-DD", str(ctx.exception))

    def test_empty_string_raises(self) -> None:
        with self.assertRaises(ValidationError):
            parse_date("")


class TestValidateLot(unittest.TestCase):
    def test_valid_lot_returns_dates(self) -> None:
        lot = RSULot(
            ticker="AAPL",
            units=100,
            date_bought="2023-01-15",
            date_sold="2024-03-01",
        )
        d_bought, d_sold = validate_lot(lot, 0)
        self.assertEqual(d_bought, datetime(2023, 1, 15))
        self.assertEqual(d_sold, datetime(2024, 3, 1))

    def test_empty_ticker_raises(self) -> None:
        lot = RSULot(ticker="", units=100, date_bought="2023-01-15", date_sold="2024-03-01")
        with self.assertRaises(ValidationError) as ctx:
            validate_lot(lot, 0)
        self.assertIn("Ticker", str(ctx.exception))

    def test_zero_units_raises(self) -> None:
        lot = RSULot(ticker="AAPL", units=0, date_bought="2023-01-15", date_sold="2024-03-01")
        with self.assertRaises(ValidationError) as ctx:
            validate_lot(lot, 0)
        self.assertIn("positive", str(ctx.exception))

    def test_buy_after_sell_raises(self) -> None:
        lot = RSULot(ticker="AAPL", units=100, date_bought="2024-03-01", date_sold="2023-01-15")
        with self.assertRaises(ValidationError) as ctx:
            validate_lot(lot, 0)
        self.assertIn("before sell", str(ctx.exception))

    def test_same_buy_sell_date_raises(self) -> None:
        lot = RSULot(ticker="AAPL", units=100, date_bought="2024-01-15", date_sold="2024-01-15")
        with self.assertRaises(ValidationError):
            validate_lot(lot, 0)
