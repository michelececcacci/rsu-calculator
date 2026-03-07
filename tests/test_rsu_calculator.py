import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd

from src.models import Transaction, TransactionAction
from src.price_fetcher import PriceFetcher
from src.rsu_calculator import calculate_rsu_metrics, match_transactions


class TestRSUCalculator(unittest.TestCase):

    def test_match_transactions_full_sell(self):
        tx1 = Transaction(date=datetime(2023, 1, 15), action=TransactionAction.VEST, quantity=50, symbol="AAPL")
        tx2 = Transaction(date=datetime(2023, 6, 15), action=TransactionAction.SELL, quantity=50, symbol="AAPL")
        
        data = match_transactions([tx1, tx2])
        self.assertEqual(len(data), 1)
        
        self.assertEqual(data[0]['Ticker'], 'AAPL')
        self.assertEqual(data[0]['Vest Date'], '2023-01-15')
        self.assertEqual(data[0]['Sell Date'], '2023-06-15')
        self.assertEqual(data[0]['Shares'], 50)

    def test_match_transactions_partial_sell_and_unsold(self):
        tx1 = Transaction(date=datetime(2023, 1, 15), action=TransactionAction.VEST, quantity=50, symbol="AAPL")
        tx2 = Transaction(date=datetime(2023, 3, 10), action=TransactionAction.VEST, quantity=20, symbol="GOOG")
        tx3 = Transaction(date=datetime(2023, 6, 15), action=TransactionAction.SELL, quantity=20, symbol="AAPL")
        
        data = match_transactions([tx1, tx2, tx3])
        self.assertEqual(len(data), 3)
        
        aapl_sold = [d for d in data if d['Ticker'] == 'AAPL' and d['Sell Date'] is not None]
        aapl_unsold = [d for d in data if d['Ticker'] == 'AAPL' and d['Sell Date'] is None]
        goog_unsold = [d for d in data if d['Ticker'] == 'GOOG' and d['Sell Date'] is None]
        
        self.assertEqual(len(aapl_sold), 1)
        self.assertEqual(aapl_sold[0]['Shares'], 20)
        
        self.assertEqual(len(aapl_unsold), 1)
        self.assertEqual(aapl_unsold[0]['Shares'], 30)
        
        self.assertEqual(len(goog_unsold), 1)
        self.assertEqual(goog_unsold[0]['Shares'], 20)

    @patch('src.price_fetcher.yf.Ticker')
    def test_get_historical_price(self, mock_ticker):
        mock_hist_df = pd.DataFrame(
            {'Close': [150.0]},
            index=pd.to_datetime(['2023-01-13'])
        )
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist_df
        mock_ticker.return_value = mock_instance

        price = PriceFetcher.get_historical_price("AAPL", "2023-01-13")
        
        self.assertEqual(price, 150.0)
        mock_instance.history.assert_called_once_with(start="2023-01-13", end="2023-01-14")

    def test_calculate_rsu_metrics_with_sell(self):
        def mock_price_fetcher(ticker, date_str):
            mapping = {
                ('AAPL', '2023-01-15'): 100.0,
                ('AAPL', '2023-06-15'): 120.0,
            }
            return mapping.get((ticker, date_str))
            
        def mock_rate_fetcher(date_str, base_currency="EUR", target_currency="USD"):
            mapping = {
                '2023-01-15': 0.90,
                '2023-06-15': 0.95,
            }
            return mapping.get(date_str)
        
        data = [{
            'Ticker': 'AAPL',
            'Vest Date': '2023-01-15',
            'Sell Date': '2023-06-15',
            'Shares': 50
        }]
        
        results = calculate_rsu_metrics(data, price_fetcher=mock_price_fetcher, rate_fetcher=mock_rate_fetcher)
        
        self.assertEqual(len(results), 1)
        res = results[0]
        
        # Verify Prices
        self.assertEqual(res['Vest Price (USD)'], 100.0)
        self.assertEqual(res['Sell Price (USD)'], 120.0)
        
        # Cost Basis = 50 * 100 = 5000 USD. EUR = 5000 * 0.90 = 4500 EUR
        self.assertEqual(res['Cost Basis (USD)'], 5000.0)
        self.assertEqual(res['Cost Basis (EUR)'], 4500.0)
        
        # Proceeds = 50 * 120 = 6000 USD. EUR = 6000 * 0.95 = 5700 EUR
        self.assertEqual(res['Proceeds (USD)'], 6000.0)
        self.assertEqual(res['Proceeds (EUR)'], 5700.0)
        
        # Gain = Proceeds - Cost Basis
        self.assertEqual(res['Gain (USD)'], 1000.0)
        self.assertEqual(res['Gain (EUR)'], 1200.0)

    def test_calculate_rsu_metrics_no_sell(self):
        def mock_price_fetcher(ticker, date_str):
            mapping = {
                ('GOOG', '2023-03-10'): 50.0,
            }
            return mapping.get((ticker, date_str))
            
        def mock_rate_fetcher(date_str, base_currency="EUR", target_currency="USD"):
            mapping = {
                '2023-03-10': 0.90,
            }
            return mapping.get(date_str)
        
        data = [{
            'Ticker': 'GOOG',
            'Vest Date': '2023-03-10',
            'Sell Date': None,
            'Shares': 20
        }]
        
        results = calculate_rsu_metrics(data, price_fetcher=mock_price_fetcher, rate_fetcher=mock_rate_fetcher)
        self.assertEqual(len(results), 1)
        res = results[0]
        
        # Cost Basis = 20 * 50 = 1000 USD. EUR = 900 EUR
        self.assertEqual(res['Cost Basis (USD)'], 1000.0)
        self.assertEqual(res['Cost Basis (EUR)'], 900.0)
        
        self.assertEqual(res['Proceeds (USD)'], 0.0)
        self.assertEqual(res['Proceeds (EUR)'], 0.0)
        self.assertEqual(res['Gain (USD)'], 0.0)
        self.assertEqual(res['Gain (EUR)'], 0.0)


if __name__ == '__main__':
    unittest.main()
