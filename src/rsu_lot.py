from dataclasses import dataclass

@dataclass
class RSULot:
    """A single RSU lot: ticker, units, date bought, date sold."""

    ticker: str
    units: int
    date_bought: str  # YYYY-MM-DD
    date_sold: str     # YYYY-MM-DD