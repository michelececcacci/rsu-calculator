from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional, Union

import pandas as pd

# Default path to the FX rates file, relative to the project root
DEFAULT_FX_RATES_PATH = Path(__file__).parent.parent / "assets" / "fxrates.xls"


class FxRateCalculator:
    """Loads ECB FX rate data from an XLS file and provides rate lookups by date.

    The XLS file is expected to have:
      - Row 0: currency codes (USD, JPY, CHF, etc.)
      - Rows 1+: daily FX rates (EUR-based)
      - Column 'Unnamed: 1' as the date column
    """

    def __init__(self, file_path: Union[str, Path] = DEFAULT_FX_RATES_PATH) -> None:
        self._file_path = Path(file_path)
        self._rates: pd.DataFrame = self._load()

    def _load(self) -> pd.DataFrame:
        """Load and clean the XLS file into a DatetimeIndex-ed DataFrame of Decimals."""
        raw = pd.read_excel(self._file_path)

        # Row 0 contains currency codes — extract them to build clean column names
        currency_codes = raw.iloc[0, 2:].tolist()  # skip first two unnamed columns

        # Data rows start at index 1; dates are in the second column ('Unnamed: 1')
        data = raw.iloc[1:].copy()
        data = data.rename(columns={"Unnamed: 1": "Date"})

        # Keep only the date column + rate columns
        rate_columns = raw.columns[2:].tolist()
        data = data[["Date"] + rate_columns]

        # Rename rate columns to their currency codes
        rename_map = dict(zip(rate_columns, currency_codes))
        data = data.rename(columns=rename_map)

        # Parse dates and set as index
        data["Date"] = pd.to_datetime(data["Date"])
        data = data.set_index("Date")
        data = data.sort_index()

        # Convert rate values to Decimal, keeping missing values as None
        def to_decimal(value: object) -> Optional[Decimal]:
            if pd.isna(value):
                return None
            return Decimal(str(value))

        data = data.map(to_decimal)

        return data

    @staticmethod
    def _to_timestamp(target_date: Union[str, date, datetime]) -> pd.Timestamp:
        """Normalise supported date representations into a pandas Timestamp."""
        if isinstance(target_date, str):
            target_date = pd.to_datetime(target_date)
        elif isinstance(target_date, date) and not isinstance(target_date, datetime):
            target_date = datetime.combine(target_date, datetime.min.time())

        return pd.Timestamp(target_date)

    @property
    def currencies(self) -> list[str]:
        """Return the list of available currency codes."""
        return self._rates.columns.tolist()

    @property
    def date_range(self) -> tuple[datetime, datetime]:
        """Return the (earliest, latest) dates available."""
        return self._rates.index.min(), self._rates.index.max()

    def _ensure_currency(self, currency: str) -> str:
        """Validate that a currency is available and return its normalized code."""
        code = currency.upper()
        if code not in self._rates.columns:
            raise ValueError(
                f"Currency '{code}' not found. Available currencies: {self.currencies}"
            )
        return code

    def get_rate(self, currency: str, target_date: Union[str, date, datetime]) -> Decimal:
        """Get the EUR→currency exchange rate for the given date.

        Args:
            currency: Currency code (e.g. 'USD', 'CHF', 'GBP').
            target_date: The date to look up.

        Returns:
            The FX rate as a Decimal.

        Raises:
            ValueError: If the currency is not found or no rate is available for the date.
        """
        code = self._ensure_currency(currency)
        target_ts = self._to_timestamp(target_date)

        if target_ts in self._rates.index:
            rate = self._rates.loc[target_ts, code]
            if rate is not None:
                return rate

        raise ValueError(
            f"No FX rate available for {code} on {target_ts.date()}. "
            f"Data covers {self.date_range[0].date()} to {self.date_range[1].date()}."
        )
