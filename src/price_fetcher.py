"""Price data fetching with error handling and retries."""

import time
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

import pandas as pd
import yfinance as yf

from src.exceptions import NetworkError, PriceDataError

TWO_PLACES = Decimal("0.01")
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2.0


def _get_price_column(hist: pd.DataFrame) -> Optional[str]:
    """Return the price column name (Close or Adj Close)."""
    if hist.empty:
        return None
    if "Close" in hist.columns:
        return "Close"
    if "Adj Close" in hist.columns:
        return "Adj Close"
    return None


def get_price_for_date(
    ticker: Any,
    d: date,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY_SEC,
) -> Optional[Decimal]:
    """
    Fetch adjusted close price for a single date.
    Assumes the market is open on the transaction date.
    Returns Decimal for precise monetary use; None if no data.
    Raises NetworkError on repeated fetch failures.
    """
    start = d.strftime("%Y-%m-%d")
    end = (datetime.combine(d, datetime.min.time()) + timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            hist = ticker.history(start=start, end=end, auto_adjust=True)
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise NetworkError(
                    f"Failed to fetch price data after {max_retries} attempts: {e}",
                    cause=last_error,
                ) from e
    else:
        hist = pd.DataFrame()

    if hist.empty:
        return None

    price_col = _get_price_column(hist)
    if price_col is None:
        return None

    val = hist[price_col].iloc[0]
    if val != val or val <= 0:  # NaN or invalid
        return None

    return Decimal(str(float(val))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def fetch_price_for_date(
    ticker_symbol: str,
    d: date,
    lot_index: Optional[int] = None,
    date_label: str = "",
) -> Decimal:
    """
    Fetch price for a ticker on a date. Raises PriceDataError or NetworkError
    on failure. Returns Decimal on success.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
    except Exception as e:
        raise NetworkError(
            f"Failed to create ticker for '{ticker_symbol}': {e}",
            cause=e,
        ) from e

    price = get_price_for_date(ticker, d)
    if price is None:
        raise PriceDataError(
            f"No price data for {ticker_symbol} on or near {date_label or d}. "
            "Check ticker symbol and date (weekends/holidays may have no data).",
            ticker=ticker_symbol,
            date_str=str(d),
            lot_index=lot_index,
        )
    return price


def get_usd_to_currency_rate_for_date(
    ticker_symbol: str,
    d: date,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY_SEC,
) -> Optional[Decimal]:
    """
    Fetch USD-to-foreign rate for a specific date from yfinance.
    For XXXUSD pairs (USD quote): returns USD per 1 XXX → divide usd_amount by rate.
    For USDXXX pairs (USD base): returns XXX per 1 USD → multiply usd_amount by rate.
    Uses nearest available rate if exact date has no data (e.g. weekends).
    Returns None if no data; does not raise (FX is optional display).
    """
    start = (datetime.combine(d, datetime.min.time()) - timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    end = (datetime.combine(d, datetime.min.time()) + timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            t = yf.Ticker(ticker_symbol)
            hist = t.history(start=start, end=end, auto_adjust=True)
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                # FX fetch fails silently - we don't want to break the main flow
                return None
    else:
        return None

    if hist.empty:
        return None

    price_col = _get_price_column(hist)
    if price_col is None:
        return None

    val = hist[price_col].iloc[-1]
    if val != val or val <= 0:
        return None

    return Decimal(str(float(val))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
