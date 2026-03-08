import csv
import re
from datetime import datetime
from decimal import Decimal
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
                print(row)
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
            term=row["Term"],
            unadjusted_cost_basis=SchwabTransactionReader._parse_decimal(
                row["Unadjusted Cost Basis"]
            ),
            transaction_closed_date=SchwabTransactionReader._parse_date(
                row["Transaction Closed Date"]
            ),
        )

    @staticmethod
    def _parse_decimal(value: str) -> Decimal:
        clean_val = re.sub(r"[$,%]", "", value).replace(",", "")
        return Decimal(clean_val)

    @staticmethod
    def _parse_date(value: str) -> datetime:
        return datetime.strptime(value, "%m/%d/%Y")
