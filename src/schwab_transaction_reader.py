import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from src.models import SchwabRealizedLot


class SchwabTransactionReader:
    @staticmethod
    def parse_file(file_path: str) -> List[SchwabRealizedLot]:
        with open(file_path, mode="r", encoding="utf-8") as f:
            # Skip the first metadata row
            next(f)

            # Use DictReader for the actual header row
            reader = csv.DictReader(f)
            lots: List[SchwabRealizedLot] = []

            for row in reader:
                # Some rows might be empty or invalid
                if not row.get("Symbol"):
                    continue

                lots.append(SchwabTransactionReader._parse_row(row))

            return lots

    @staticmethod
    def _parse_row(row: dict) -> SchwabRealizedLot:
        return SchwabRealizedLot(
            symbol=row.get("Symbol", ""),
            name=row.get("Name", ""),
            closed_date=SchwabTransactionReader._parse_date(row.get("Closed Date")),
            opened_date=SchwabTransactionReader._parse_date(row.get("Opened Date")),
            quantity=SchwabTransactionReader._parse_decimal(row.get("Quantity")),
            proceeds_per_share=SchwabTransactionReader._parse_decimal(
                row.get("Proceeds Per Share")
            ),
            cost_per_share=SchwabTransactionReader._parse_decimal(row.get("Cost Per Share")),
            proceeds=SchwabTransactionReader._parse_decimal(row.get("Proceeds")),
            cost_basis=SchwabTransactionReader._parse_decimal(row.get("Cost Basis (CB)")),
            gain_loss_dollars=SchwabTransactionReader._parse_decimal(row.get("Gain/Loss ($)")),
            gain_loss_percent=SchwabTransactionReader._parse_decimal(row.get("Gain/Loss (%)")),
            long_term_gain_loss=SchwabTransactionReader._parse_decimal(
                row.get("Long Term Gain/Loss")
            ),
            short_term_gain_loss=SchwabTransactionReader._parse_decimal(
                row.get("Short Term Gain/Loss")
            ),
            term=row.get("Term", ""),
            unadjusted_cost_basis=SchwabTransactionReader._parse_decimal(
                row.get("Unadjusted Cost Basis")
            ),
            wash_sale=row.get("Wash Sale?", "").lower() == "yes",
            disallowed_loss=SchwabTransactionReader._parse_decimal(row.get("Disallowed Loss")),
            transaction_closed_date=SchwabTransactionReader._parse_date(
                row.get("Transaction Closed Date")
            ),
            transaction_cost_basis=SchwabTransactionReader._parse_decimal(
                row.get("Transaction Cost Basis")
            ),
            total_transaction_gain_loss_dollars=SchwabTransactionReader._parse_decimal(
                row.get("Total Transaction Gain/Loss ($)")
            ),
            total_transaction_gain_loss_percent=SchwabTransactionReader._parse_decimal(
                row.get("Total Transaction Gain/Loss (%)")
            ),
            lt_transaction_gain_loss_dollars=SchwabTransactionReader._parse_decimal(
                row.get("LT Transaction Gain/Loss ($)")
            ),
            lt_transaction_gain_loss_percent=SchwabTransactionReader._parse_decimal(
                row.get("LT Transaction Gain/Loss (%)")
            ),
            st_transaction_gain_loss_dollars=SchwabTransactionReader._parse_decimal(
                row.get("ST Transaction Gain/Loss ($)")
            ),
            st_transaction_gain_loss_percent=SchwabTransactionReader._parse_decimal(
                row.get("ST Transaction Gain/Loss (%)")
            ),
        )

    @staticmethod
    def _parse_decimal(value: Optional[str]) -> Decimal:
        if not value or value.strip() == "":
            return Decimal("0.0")
        # Remove $, %, and commas
        clean_val = re.sub(r"[$,%]", "", value).replace(",", "")
        try:
            return Decimal(clean_val)
        except (ValueError, InvalidOperation):
            return Decimal("0.0")

    @staticmethod
    def _parse_date(value: Optional[str]) -> datetime:
        if not value or value.strip() == "":
            return datetime.min

        # Try DD/MM/YYYY and MM/DD/YYYY
        # In the sample '13/03/2024' and '10/20/2024' are present.
        for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        return datetime.min
