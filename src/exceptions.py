"""Custom exceptions for the RSU calculator."""

from typing import Optional


class RSUCalculatorError(Exception):
    """Base exception for RSU calculator errors."""

    pass


class ValidationError(RSUCalculatorError):
    """Raised when input validation fails (dates, units, ticker, etc.)."""

    def __init__(self, message: str, lot_index: Optional[int] = None) -> None:
        self.lot_index = lot_index
        super().__init__(message)


class PriceDataError(RSUCalculatorError):
    """Raised when price data cannot be fetched (no data, invalid ticker)."""

    def __init__(
        self,
        message: str,
        ticker: Optional[str] = None,
        date_str: Optional[str] = None,
        lot_index: Optional[int] = None,
    ) -> None:
        self.ticker = ticker
        self.date_str = date_str
        self.lot_index = lot_index
        super().__init__(message)


class NetworkError(RSUCalculatorError):
    """Raised when a network/API request fails."""

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        self.cause = cause
        super().__init__(message)
