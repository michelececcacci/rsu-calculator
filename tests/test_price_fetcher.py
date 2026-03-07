from src.price_fetcher import PriceFetcher
import unittest

class TestPriceFetcher(unittest.TestCase):
    def test_get_historical_price_goog(self):
        self.assertAlmostEqual(311.76, PriceFetcher.get_historical_price("GOOGL", "2026-02-27"), 4)

    def test_historical_price_aapl(self):
        self.assertAlmostEqual(264.18, PriceFetcher.get_historical_price("AAPL", "2026-02-27"), 4)
