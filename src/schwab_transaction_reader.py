import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List

from src.models import SchwabRealizedLot


class SchwabTransactionReader:
    @staticmethod
    def parse_file(file_path: str) -> List[SchwabRealizedLot]:
        with open(file_path, mode="r", encoding="utf-8") as f:
            # Skip the first metadata row
            next(f)

            reader = csv.DictReader(f)
            lots: List[SchwabRealizedLot] = []

            for row in reader:
                lots.append(SchwabTransactionReader._parse_row(row))

            return lots

    @staticmethod
    def _parse_row(row: dict) -> SchwabRealizedLot:
        return SchwabRealizedLot(
            symbol=row["Symbol"],
            name=row["Name"],
            closed_date=SchwabTransactionReader._parse_date(row["Closed Date"]),
            opened_date=SchwabTransactionReader._parse_date(row["Opened Date"]),
            quantity=SchwabTransactionReader._parse_decimal(row["Quantity"]),
            proceeds_per_share=SchwabTransactionReader._parse_decimal(row["Proceeds Per Share"]),
            cost_per_share=SchwabTransactionReader._parse_decimal(row["Cost Per Share"]),
            proceeds=SchwabTransactionReader._parse_decimal(row["Proceeds"]),
            cost_basis=SchwabTransactionReader._parse_decimal(row["Cost Basis (CB)"]),
            gain_loss_dollars=SchwabTransactionReader._parse_decimal(row["Gain/Loss ($)"]),
            long_term_gain_loss=SchwabTransactionReader._parse_decimal(row["Long Term Gain/Loss"]),
            short_term_gain_loss=SchwabTransactionReader._parse_decimal(
                row["Short Term Gain/Loss"]
            ),
            term=row["Term"],
            unadjusted_cost_basis=SchwabTransactionReader._parse_decimal(
                row["Unadjusted Cost Basis"]
            ),
            disallowed_loss=SchwabTransactionReader._parse_decimal(row["Disallowed Loss"]),
            transaction_closed_date=SchwabTransactionReader._parse_date(
                row["Transaction Closed Date"]
            ),
            transaction_cost_basis=SchwabTransactionReader._parse_decimal(
                row["Transaction Cost Basis"]
            ),
            total_transaction_gain_loss_dollars=SchwabTransactionReader._parse_decimal(
                row["Total Transaction Gain/Loss ($)"]
            ),
        )

    @staticmethod
    def _parse_decimal(value: str) -> Decimal:
        clean_val = re.sub(r"[$,%]", "", value).replace(",", "")
        try:
            return Decimal(clean_val)
        except (ValueError, InvalidOperation) as e:
            print(f"exception {e} for {clean_val}")
            return Decimal("0.0")

    @staticmethod
    def _parse_date(value: str) -> datetime:
        return datetime.strptime(value, "%m/%d/%Y")
