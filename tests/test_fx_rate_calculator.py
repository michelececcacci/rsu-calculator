import unittest
from datetime import datetime
from decimal import Decimal

from src.fx_rate_calculator import FxRateCalculator


class TestFxRateCalculator(unittest.TestCase):
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
