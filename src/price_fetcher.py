from datetime import datetime, timedelta

import yfinance as yf


class PriceFetcher:
    @staticmethod
    def get_historical_price(ticker_symbol: str, date_str: str) -> float:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        next_day_str = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(start=date_str, end=next_day_str)

        if hist.empty:
            raise ValueError(f"No price data found for {ticker_symbol} on {date_str}.")

        return hist["Close"].iloc[0]
