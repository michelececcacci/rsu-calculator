from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TransactionAction(Enum):
    VEST = "Vest"
    SELL = "Sell"


@dataclass
class Transaction:
    date: datetime
    action: TransactionAction
    quantity: Decimal
    symbol: str
    price: Decimal = Decimal("0.0")  # Optional, can be fetched later or parsed if available


@dataclass
class SchwabRealizedLot:
    symbol: str
    name: str
    closed_date: datetime
    opened_date: datetime
    quantity: Decimal
    proceeds_per_share: Decimal
    cost_per_share: Decimal
    proceeds: Decimal
    cost_basis: Decimal
    gain_loss_dollars: Decimal
    gain_loss_percent: Decimal
    long_term_gain_loss: Decimal
    short_term_gain_loss: Decimal
    term: str
    unadjusted_cost_basis: Decimal
    wash_sale: bool
    disallowed_loss: Decimal
    transaction_closed_date: datetime
    transaction_cost_basis: Decimal
    total_transaction_gain_loss_dollars: Decimal
    total_transaction_gain_loss_percent: Decimal
    lt_transaction_gain_loss_dollars: Decimal
    lt_transaction_gain_loss_percent: Decimal
    st_transaction_gain_loss_dollars: Decimal
    st_transaction_gain_loss_percent: Decimal
