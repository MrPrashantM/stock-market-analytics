"""
Step 1: Data Collection
========================
Real stock data fetch karna yfinance se.
Stocks: Top Indian + US companies
Period: 2 years ka data
"""

import yfinance as yf
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_PATH = r"C:\Users\DELL\stock_analytics\data"
os.makedirs(DATA_PATH, exist_ok=True)

# ── Stocks to fetch ───────────────────────────────────────────────────────────
STOCKS = {
    # Indian Stocks (NSE)
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS":      "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank",
    "INFY.NS":     "Infosys",
    "WIPRO.NS":    "Wipro",
    # US Stocks
    "AAPL":  "Apple",
    "MSFT":  "Microsoft",
    "GOOGL": "Google",
}

PERIOD = "2y"   # 2 years data
INTERVAL = "1d" # daily

print("=" * 55)
print("  STEP 1 — STOCK DATA COLLECTION")
print("=" * 55)

all_data = []

for ticker, name in STOCKS.items():
    try:
        print(f"\n📥 Fetching {name} ({ticker})...")
        stock = yf.Ticker(ticker)
        df    = stock.history(period=PERIOD, interval=INTERVAL)

        if df.empty:
            print(f"   ⚠️  No data found for {ticker}")
            continue

        df = df.reset_index()
        df["Ticker"] = ticker
        df["Company"] = name
        df["Market"]  = "India" if ".NS" in ticker else "US"

        # Keep only useful columns
        df = df[["Date","Ticker","Company","Market",
                 "Open","High","Low","Close","Volume"]]
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

        all_data.append(df)
        print(f"   ✅ {len(df)} rows fetched | "
              f"Latest close: {df['Close'].iloc[-1]:.2f}")

    except Exception as e:
        print(f"   ❌ Error fetching {ticker}: {e}")

# ── Combine & Save ────────────────────────────────────────────────────────────
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    out_path = os.path.join(DATA_PATH, "stocks_raw.csv")
    final_df.to_csv(out_path, index=False)

    print("\n" + "=" * 55)
    print(f"  ✅ Data saved → {out_path}")
    print(f"  Total rows    : {len(final_df):,}")
    print(f"  Stocks        : {final_df['Ticker'].nunique()}")
    print(f"  Date range    : {final_df['Date'].min()} → {final_df['Date'].max()}")
    print("=" * 55)
else:
    print("\n❌ No data fetched. Check internet connection.")