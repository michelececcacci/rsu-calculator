import os
import unittest
from datetime import datetime

from src.models import TransactionAction
from src.schwab_json_parser import SchwabJsonParser


class TestSchwabJsonParser(unittest.TestCase):
    def test_load_schwab_data_json(self):
        # Get the path to schwab_data.json relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "schwab_data.json")

        transactions = SchwabJsonParser.parse_file(json_path)

        # schwab_data.json has 2 relevant transactions (one Sell, one Stock Plan Activity)
        self.assertEqual(len(transactions), 2)

        # Transactions should be sorted by date
        vest_tx = transactions[0]  # 11/21/2024
        self.assertEqual(vest_tx.action, TransactionAction.VEST)
        self.assertEqual(vest_tx.date, datetime(2024, 11, 21))
        self.assertEqual(vest_tx.quantity, 30)
        self.assertEqual(vest_tx.symbol, "GOOGL")

        sell_tx = transactions[1]  # 12/03/2024
        self.assertEqual(sell_tx.action, TransactionAction.SELL)
        self.assertEqual(sell_tx.date, datetime(2024, 12, 3))
        self.assertEqual(sell_tx.quantity, 30.0)
        self.assertEqual(sell_tx.symbol, "GOOGL")

    def test_ignores_credit_interest_and_wire_sent(self):
        json_data = {
            "BrokerageTransactions": [
                {
                    "Date": "12/01/2024",
                    "Action": "Credit Interest",
                    "Symbol": "GOOGL",
                    "Description": "interest on cash balance",
                    "Quantity": "10",
                },
                {
                    "Date": "12/02/2024",
                    "Action": "Wire Sent",
                    "Symbol": "GOOGL",
                    "Description": "outgoing wire",
                    "Quantity": "5",
                },
                {
                    "Date": "12/03/2024",
                    "Action": "Sell",
                    "Symbol": "GOOGL",
                    "Description": "RSU sale",
                    "Quantity": "30",
                },
            ]
        }

        transactions = SchwabJsonParser.parse_data(json_data)

        # Only the Sell should be parsed into a Transaction
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].action, TransactionAction.SELL)
        self.assertEqual(transactions[0].quantity, 30)
        self.assertEqual(transactions[0].symbol, "GOOGL")


if __name__ == "__main__":
    unittest.main()
