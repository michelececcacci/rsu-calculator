import unittest
import os
from datetime import datetime

from src.schwab_json_parser import SchwabJsonParser
from src.models import TransactionAction

class TestSchwabJsonParser(unittest.TestCase):
    def test_load_schwab_data_json(self):
        # Get the path to schwab_data.json relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, 'schwab_data.json')
        
        transactions = SchwabJsonParser.parse_file(json_path)
        
        # schwab_data.json has 2 relevant transactions (one Sell, one Stock Plan Activity)
        self.assertEqual(len(transactions), 2)
        
        # Transactions should be sorted by date
        vest_tx = transactions[0] # 11/21/2024
        self.assertEqual(vest_tx.action, TransactionAction.VEST)
        self.assertEqual(vest_tx.date, datetime(2024, 11, 21))
        self.assertEqual(vest_tx.quantity, 30)
        self.assertEqual(vest_tx.symbol, "GOOGL")
        
        sell_tx = transactions[1] # 12/03/2024
        self.assertEqual(sell_tx.action, TransactionAction.SELL)
        self.assertEqual(sell_tx.date, datetime(2024, 12, 3))
        self.assertEqual(sell_tx.quantity, 30.0)
        self.assertEqual(sell_tx.symbol, "GOOGL")

if __name__ == '__main__':
    unittest.main()
