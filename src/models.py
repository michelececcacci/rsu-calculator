from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

class TransactionAction(Enum):
    VEST = "Vest"
    SELL = "Sell"

@dataclass
class Transaction:
    date: datetime
    action: TransactionAction
    quantity: int
    symbol: str
    price: float = 0.0  # Optional, can be fetched later or parsed if available
