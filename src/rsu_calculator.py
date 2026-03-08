import argparse
import sys

from src.schwab_transaction_reader import SchwabTransactionReader


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate Cost Basis and Gains for RSUs in EUR.")
    parser.add_argument("file", help="Path to the input CSV or JSON file")
    args = parser.parse_args()

    try:
        schwab_transactions = SchwabTransactionReader.parse_file(args.file)
        print(f"Successfully parsed {len(schwab_transactions)} lots.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
