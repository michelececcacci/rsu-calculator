import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from src.fx_rate_calculator import FxRateCalculator


class TestFxRateCalculator(unittest.TestCase):
    def test_get_rate_and_nearest_use_decimal_for_eur_usd(self) -> None:
        calc = FxRateCalculator()  # Uses the real XLS asset
        self.assertIn("USD", calc.currencies)

        usd_series = calc._rates["USD"].dropna()  # type: ignore[attr-defined]
        self.assertFalse(usd_series.empty)

        # Use the first and last available USD dates from the real data
        first_date = usd_series.index[0]
        last_date = usd_series.index[-1]
        expected_first = usd_series.iloc[0]
        expected_last = usd_series.iloc[-1]

        # Exact-date lookups with different input types all match stored Decimal
        rate_str = calc.get_rate("usd", first_date.strftime("%Y-%m-%d"))
        rate_dt = calc.get_rate("USD", first_date.to_pydatetime())
        rate_date = calc.get_rate("USD", first_date.date())
        for rate in (rate_str, rate_dt, rate_date):
            self.assertIsInstance(rate, Decimal)
            self.assertEqual(rate, expected_first)

        # Nearest-date before range should snap to earliest available date
        before_first = (first_date - timedelta(days=1)).date()
        nearest_rate_before, used_before = calc.get_rate_nearest("usd", before_first)
        self.assertIsInstance(nearest_rate_before, Decimal)
        self.assertEqual(nearest_rate_before, expected_first)
        self.assertEqual(used_before, first_date.to_pydatetime())

        # Nearest-date after range should snap to latest available date
        after_last = last_date + timedelta(days=1)
        nearest_rate_after, used_after = calc.get_rate_nearest("usd", after_last)
        self.assertIsInstance(nearest_rate_after, Decimal)
        self.assertEqual(nearest_rate_after, expected_last)
        self.assertEqual(used_after, last_date.to_pydatetime())

    def test_real_file_has_usd_decimal_rates(self) -> None:
        calc = FxRateCalculator()  # Uses the default XLS asset
        self.assertIn("USD", calc.currencies)

        # Check a few specific calendar dates where we know data exists
        cases = {
            "2016-01-04": Decimal("1.0898"),
            "2021-02-05": Decimal("1.1983"),
            "2026-03-06": Decimal("1.1561"),
        }

        for date_str, expected in cases.items():
            # String input
            rate_str = calc.get_rate("USD", date_str)
            # date and datetime inputs
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            rate_date = calc.get_rate("USD", d)
            rate_dt = calc.get_rate("USD", datetime(d.year, d.month, d.day))

            for rate in (rate_str, rate_date, rate_dt):
                self.assertIsInstance(rate, Decimal)
                self.assertEqual(rate, expected)


if __name__ == "__main__":
    unittest.main()
