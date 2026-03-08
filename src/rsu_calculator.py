import argparse
import sys

from src.fx_rate_calculator import FxRateCalculator
from src.schwab_transaction_reader import SchwabTransactionReader


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate Cost Basis and Gains for RSUs in EUR.")
    parser.add_argument("file", help="Path to the input CSV or JSON file")
    args = parser.parse_args()
    fx_rate_calculator = FxRateCalculator()

    try:
        schwab_transactions = SchwabTransactionReader.parse_file(args.file)
        total_cost_basis_usd = 0
        total_proceeds_usd = 0
        total_proceeds_eur = 0
        total_cost_basis_eur = 0
        for transaction in schwab_transactions:
            eur_to_usd_sell_rate = fx_rate_calculator.get_rate("USD", transaction.closed_date)
            eur_to_usd_buy_rate = fx_rate_calculator.get_rate("USD", transaction.opened_date)
            total_cost_basis_usd += transaction.cost_basis
            total_proceeds_usd += transaction.proceeds
            total_proceeds_eur += transaction.proceeds / eur_to_usd_sell_rate
            total_cost_basis_eur += transaction.cost_basis / eur_to_usd_buy_rate
        print(f"Total cost basis (USD): {total_cost_basis_usd}")
        print(f"Total proceeds (USD): {total_proceeds_usd}")
        print(f"Total cost basis (EUR): {total_cost_basis_eur}")
        print(f"Total proceeds (EUR): {total_proceeds_eur}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
