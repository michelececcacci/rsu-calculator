"""Input validation for RSU lots and dates."""

from datetime import datetime
from typing import Tuple

from src.exceptions import ValidationError
from src.rsu_lot import RSULot


def parse_date(date_str: str, context: str = "") -> datetime:
    """
    Parse date string in YYYY-MM-DD format.
    Raises ValidationError if format is invalid.
    """
    if not date_str or not isinstance(date_str, str):
        raise ValidationError(
            f"Date cannot be empty. Use YYYY-MM-DD format."
            + (f" ({context})" if context else "")
        )
    stripped = date_str.strip()
    if not stripped:
        raise ValidationError(
            f"Date cannot be empty. Use YYYY-MM-DD format."
            + (f" ({context})" if context else "")
        )
    try:
        return datetime.strptime(stripped, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(
            f"Invalid date format: '{date_str}'. Use YYYY-MM-DD."
            + (f" ({context})" if context else "")
        )


def validate_lot(
    lot: RSULot, lot_index: int
) -> Tuple[datetime, datetime]:
    """
    Validate an RSU lot. Raises ValidationError on failure.
    """
    if not isinstance(lot, RSULot):
        raise ValidationError(
            f"Expected RSULot instance, got {type(lot).__name__}.",
            lot_index=lot_index,
        )

    ticker = getattr(lot, "ticker", None)
    if not ticker or not str(ticker).strip():
        raise ValidationError(
            f"Ticker symbol cannot be empty.",
            lot_index=lot_index,
        )

    units = getattr(lot, "units", None)
    if units is None:
        raise ValidationError(
            f"Units must be specified.",
            lot_index=lot_index,
        )
    try:
        units_int = int(units)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Units must be a positive integer, got '{units}'.",
            lot_index=lot_index,
        )
    if units_int <= 0:
        raise ValidationError(
            f"Units must be positive, got {units_int}.",
            lot_index=lot_index,
        )

    try:
        date_bought = parse_date(
            getattr(lot, "date_bought", ""),
            context=f"lot {lot_index + 1} buy date",
        )
    except ValidationError as e:
        e.lot_index = lot_index
        raise

    try:
        date_sold = parse_date(
            getattr(lot, "date_sold", ""),
            context=f"lot {lot_index + 1} sell date",
        )
    except ValidationError as e:
        e.lot_index = lot_index
        raise

    if date_bought >= date_sold:
        raise ValidationError(
            f"Buy date must be before sell date "
            f"({lot.date_bought} >= {lot.date_sold}).",
            lot_index=lot_index,
        )
    return date_bought, date_sold
