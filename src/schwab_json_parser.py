import json
from datetime import datetime
from typing import List

from src.models import Transaction, TransactionAction


class SchwabJsonParser:
    @staticmethod
    def parse_file(file_path: str) -> List[Transaction]:
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        return SchwabJsonParser.parse_data(json_data)

    @staticmethod
    def parse_data(json_data: dict) -> List[Transaction]:
        transactions_data = json_data.get("BrokerageTransactions", [])

        # Find the ticker from any transaction that has it
        ticker = "UNKNOWN"
        for t in transactions_data:
            if t.get("Symbol"):
                ticker = t["Symbol"]
                break

        transactions: List[Transaction] = []
        for t in transactions_data:
            action_raw = t.get("Action", "")
            date_raw = t.get("Date")
            if not date_raw:
                continue

            # Explicitly ignore non-RSU-related cash movements that may appear
            # in the Schwab export alongside stock plan activity.
            if action_raw in {"Credit Interest", "Wire Sent"}:
                continue

            date = datetime.strptime(date_raw, "%m/%d/%Y")
            qty = int(t.get("Quantity", 0))
            sym = t.get("Symbol", ticker)

            action = None
            if action_raw == "Stock Plan Activity":
                action = TransactionAction.VEST
            elif action_raw == "Sell":
                action = TransactionAction.SELL

            if action:
                transactions.append(Transaction(date=date, action=action, quantity=qty, symbol=sym))

        # Sort by date
        transactions.sort(key=lambda x: x.date)

        return transactions
