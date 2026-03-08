import os
import unittest
from decimal import Decimal

from src.schwab_transaction_reader import SchwabTransactionReader


class TestSchwabTransactionReader(unittest.TestCase):
    def test_parse_dummy_transactions(self):
        # Get the path to dummy_transactions.csv relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # The file is in assets/
        csv_path = os.path.join(os.path.dirname(current_dir), "assets", "dummy_transactions.csv")

        lots = SchwabTransactionReader.parse_file(csv_path)

        self.assertEqual(len(lots), 1)
        lot = lots[0]

        self.assertEqual(lot.symbol, "GOOG")
        self.assertEqual(lot.name, "GOOGLE INC A")
        self.assertEqual(lot.closed_date.month, 3)
        self.assertEqual(lot.closed_date.day, 13)
        self.assertEqual(lot.opened_date.month, 10)
        self.assertEqual(lot.opened_date.day, 20)
        self.assertEqual(lot.quantity, Decimal("30.0"))
        self.assertEqual(lot.proceeds_per_share, Decimal("50.0"))
        self.assertEqual(lot.cost_per_share, Decimal("89.23"))
        self.assertEqual(lot.proceeds, Decimal("2358.32"))
        self.assertEqual(lot.cost_basis, Decimal("2513.26"))
        self.assertEqual(lot.gain_loss_dollars, Decimal("1180.06"))
        self.assertEqual(lot.gain_loss_percent, Decimal("78.728471632106"))
        self.assertEqual(lot.short_term_gain_loss, Decimal("150.06"))
        self.assertEqual(lot.term, "Short Term")
        self.assertEqual(lot.unadjusted_cost_basis, Decimal("1912.26"))
        self.assertFalse(lot.wash_sale)
        self.assertEqual(lot.transaction_closed_date.month, 3)
        self.assertEqual(lot.transaction_closed_date.day, 13)


if __name__ == "__main__":
    unittest.main()
