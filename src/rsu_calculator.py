import argparse
import csv
import json
from datetime import datetime, timedelta
import sys

import pandas as pd
import yfinance as yf

from src.models import Transaction, TransactionAction
from src.schwab_json_parser import SchwabJsonParser


def match_transactions(transactions: list[Transaction]):
    vests = []
    sells = []
    
    for tx in transactions:
        date_str = tx.date.strftime("%Y-%m-%d")
        if tx.action == TransactionAction.VEST:
            vests.append({"Date": date_str, "Quantity": tx.quantity, "Symbol": tx.symbol, "Matched": 0})
        elif tx.action == TransactionAction.SELL:
            sells.append({"Date": date_str, "Quantity": tx.quantity, "Symbol": tx.symbol, "Matched": 0})
            
    # Sort by date
    vests.sort(key=lambda x: x["Date"])
    sells.sort(key=lambda x: x["Date"])
    
    data = []
    for vest in vests:
        vest_qty = vest["Quantity"]
        vest_sym = vest["Symbol"]
        vest_date = vest["Date"]
        
        remaining_vest = vest_qty
        for sell in sells:
            if sell["Symbol"] == vest_sym and sell["Quantity"] - sell["Matched"] > 0 and sell["Date"] >= vest_date:
                available_sell = sell["Quantity"] - sell["Matched"]
                match_qty = min(remaining_vest, available_sell)
                sell["Matched"] += match_qty
                remaining_vest -= match_qty
                
                data.append({
                    'Ticker': vest_sym,
                    'Vest Date': vest_date,
                    'Sell Date': sell["Date"],
                    'Shares': match_qty
                })
                if remaining_vest <= 0:
                    break
                    
        if remaining_vest > 0:
            data.append({
                'Ticker': vest_sym,
                'Vest Date': vest_date,
                'Sell Date': None,
                'Shares': remaining_vest
            })
            
    return data

def get_historical_price(ticker_symbol, date_str):
    """
    Fetches the adjusted close price for a ticker on a specific date.
    If the date is a weekend/holiday, queries backwards to find the closest trading day.
    """
    if not date_str:
        return None
        
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Search window of 7 days prior
    start_date_str = (date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
    next_day_str = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
    
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(start=start_date_str, end=next_day_str)
    
    if hist.empty:
        raise ValueError(f"No price data found for {ticker_symbol} around {date_str}.")
        
    # Filter out future dates (time zone issues fix)
    target_dt = pd.to_datetime(date_str).tz_localize(hist.index.tz)
    hist = hist[hist.index <= target_dt]
    
    if hist.empty:
         raise ValueError(f"No price data found for {ticker_symbol} on or before {date_str}.")
         
    close_price = hist['Close'].iloc[-1]
    return float(close_price)

def get_exchange_rate(date_str, base_currency="EUR", target_currency="USD"):
    """
    Fetches the historical exchange rate.
    USDEUR=X gets the value of 1 USD in EUR.
    """
    if not date_str:
        return None
        
    ticker_symbol = f"{target_currency}{base_currency}=X"
    return get_historical_price(ticker_symbol, date_str)


def calculate_rsu_metrics(data, price_fetcher=None, rate_fetcher=None):
    if price_fetcher is None:
        price_fetcher = get_historical_price
    if rate_fetcher is None:
        rate_fetcher = get_exchange_rate

    results = []
    for row in data:
        ticker = row['Ticker']
        shares = row['Shares']
        vest_date = row['Vest Date']
        sell_date = row['Sell Date']
        
        # Prices
        vest_price_usd = price_fetcher(ticker, vest_date)
        sell_price_usd = price_fetcher(ticker, sell_date) if sell_date else None
        
        # Forex (1 USD = X EUR) -> USDEUR=X
        usd_to_eur_vest = rate_fetcher(vest_date, base_currency="EUR", target_currency="USD")
        usd_to_eur_sell = rate_fetcher(sell_date, base_currency="EUR", target_currency="USD") if sell_date else None
        
        # Calculations
        cost_basis_usd = shares * vest_price_usd
        cost_basis_eur = cost_basis_usd * usd_to_eur_vest
        
        proceeds_usd = None
        proceeds_eur = None
        gain_eur = None
        gain_usd = None
        
        if sell_date and sell_price_usd and usd_to_eur_sell is not None:
            proceeds_usd = shares * sell_price_usd
            proceeds_eur = proceeds_usd * usd_to_eur_sell
            gain_usd = proceeds_usd - cost_basis_usd
            gain_eur = proceeds_eur - cost_basis_eur
            
        results.append({
            'Ticker': ticker,
            'Shares': shares,
            'Vest Date': vest_date,
            'Sell Date': sell_date or 'N/A',
            'Vest Price (USD)': round(vest_price_usd, 2),
            'Sell Price (USD)': round(sell_price_usd, 2) if sell_price_usd else 0.0,
            'Cost Basis (USD)': round(cost_basis_usd, 2),
            'Proceeds (USD)': round(proceeds_usd, 2) if proceeds_usd is not None else 0.0,
            'Gain (USD)': round(gain_usd, 2) if gain_usd is not None else 0.0,
            'Cost Basis (EUR)': round(cost_basis_eur, 2),
            'Proceeds (EUR)': round(proceeds_eur, 2) if proceeds_eur is not None else 0.0,
            'Gain (EUR)': round(gain_eur, 2) if gain_eur is not None else 0.0,
        })
        
    return results

def print_summary(results):
    df = pd.DataFrame(results)
    
    display_cols = [
        'Ticker', 'Shares', 'Vest Date', 'Sell Date',
        'Vest Price (USD)', 'Sell Price (USD)',
        'Cost Basis (EUR)', 'Proceeds (EUR)', 'Gain (EUR)'
    ]
    print("\n--- RSU Summary ---")
    print(df[display_cols].to_string(index=False))
    
    print("\n--- Totals ---")
    total_cost_eur = df['Cost Basis (EUR)'].sum()
    total_proceeds_eur = df['Proceeds (EUR)'].sum()
    total_gain_eur = df['Gain (EUR)'].sum()
    
    print(f"Total Cost Basis (EUR): {total_cost_eur:,.2f}")
    if any(r['Sell Date'] != 'N/A' for r in results):
        print(f"Total Proceeds (EUR)  : {total_proceeds_eur:,.2f}")
        print(f"Total Gain (EUR)      : {total_gain_eur:,.2f}")

def main():
    parser = argparse.ArgumentParser(description="Calculate Cost Basis and Gains for RSUs in EUR.")
    parser.add_argument("file", help="Path to the input CSV or JSON file")
    args = parser.parse_args()
    
    try:
        transactions = SchwabJsonParser.parse_file(args.file)
        data = match_transactions(transactions)
        results = calculate_rsu_metrics(data)
        print_summary(results)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
