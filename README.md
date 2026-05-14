# 📡 MarketLens — Stock Market Analytics Dashboard

> **Full-stack Python stock analytics project** — Real-time data, Technical Analysis, Fundamental Analysis, Pattern Recognition, and Portfolio Tracking.
> Built for portfolio / resume showcase.

---

## 🚀 Live Demo

> Deploy on Streamlit Cloud — [streamlit.io](https://streamlit.io)

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| `yfinance` | Real-time stock data (NSE/BSE/US) |
| `pandas` + `numpy` | Data processing & calculations |
| `plotly` | Interactive charts |
| `streamlit` | Dashboard UI |
| `openpyxl` | Excel export |

---

## 📁 Project Structure

```
stock_analytics/
├── src/
│   ├── generate_data.py      # Step 1: Data collection
│   ├── eda.py                # Step 2: EDA + Technical indicators
│   └── dashboard_v3.py       # Step 3: Full Streamlit dashboard
├── data/
│   ├── stocks_raw.csv        # Raw fetched data
│   └── stocks_clean.csv      # Cleaned + indicators
├── outputs/
│   ├── 01_price_trends.png
│   ├── 02_cumulative_returns.png
│   ├── 03_correlation.png
│   ├── 04_rsi.png
│   └── 05_volatility.png
├── requirements.txt
└── README.md
```

---

## ⚙️ How to Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/MrPrashantM/stock-market-analytics.git
cd stock-market-analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Fetch real stock data
python src/generate_data.py

# 4. Run EDA + save charts
python src/eda.py

# 5. Launch dashboard
streamlit run src/dashboard_v3.py
```

Dashboard opens at → **http://localhost:8501**

---

## 📊 Dashboard Features

### 🌙☀️ Dark / Light Theme
One-click toggle between dark (Bloomberg terminal style) and light mode.

### 📊 Tab 1 — Price & Volume
- Candlestick chart with real OHLCV data
- Moving Averages — MA20, MA50, MA200
- Bollinger Bands
- Volume bars (green/red based on direction)

### 📉 Tab 2 — Technical Indicators
- **RSI** (14) — Overbought/Oversold zones highlighted
- **MACD** — Line, Signal, Histogram
- **20D Rolling Volatility**
- **4 Auto Trading Signals** — RSI, MACD, MA Cross, Bollinger

### 🏢 Tab 3 — Fundamental Analysis
- **Valuation** — P/E, Forward P/E, P/B, P/S, EV/EBITDA, PEG
- **Financials** — Revenue, EBITDA, Net Income, EPS, Growth %
- **Balance Sheet** — Debt/Equity, ROE, ROA, Dividend Yield
- **Analyst Targets** — Low/Mean/High + Upside % + Recommendation

### 🔄 Tab 4 — Compare Stocks
- Compare up to 6 stocks simultaneously
- Cumulative returns chart
- Performance metrics table

### 💼 Tab 5 — Portfolio Tracker
- Enter any ticker + quantity
- Live P&L calculation
- Allocation pie chart + P&L bar chart

### 📰 Tab 6 — News Feed
- Real latest headlines via yfinance
- **Sentiment Analysis** — Auto Positive/Negative/Neutral detection
- Publisher, timestamp, article link
- Sentiment summary KPIs

### ⚡ Tab 7 — Advanced Analytics
- **Risk Metrics** — Sharpe Ratio, Sortino Ratio, Max Drawdown, VaR (95%), Calmar Ratio, Win Rate
- **Drawdown Chart** — Visual peak-to-trough analysis
- **Support & Resistance** — Auto-detected key price levels
- **Benchmark Comparison** — Stock vs NIFTY 50 / S&P 500 + Alpha
- **Export** — Download data as CSV or Excel (with Risk Metrics sheet)

### 🎯 Tab 8 — Patterns & Tools
- **Candlestick Pattern Recognition** — Doji, Hammer, Shooting Star, Bullish/Bearish Engulfing, Morning Star, Evening Star, Marubozu
- Patterns plotted on chart with ▲▼ markers
- **Volume Analysis** — OBV (On Balance Volume), Volume Spike detection (2x avg)
- **Price Target Calculator** — Entry, Stop Loss, Target → Risk/Reward ratio, Breakeven win rate, visual trade setup chart

---

## 🔍 Stocks Supported

**Indian (NSE):** RELIANCE.NS · TCS.NS · HDFCBANK.NS · INFY.NS · WIPRO.NS · TATAMOTORS.NS · ADANIENT.NS · BAJFINANCE.NS · SUNPHARMA.NS · MARUTI.NS · _any NSE ticker with .NS suffix_

**US:** AAPL · MSFT · GOOGL · AMZN · NVDA · TSLA · META · NFLX · _any US ticker_

---

## 💡 Key Technical Concepts Used

| Concept | Description |
|---|---|
| RSI | Momentum oscillator — identifies overbought/oversold |
| MACD | Trend-following — crossover signals buy/sell |
| Bollinger Bands | Volatility bands — price extremes |
| OBV | Volume-based trend confirmation |
| Sharpe Ratio | Risk-adjusted return (>1 good, >2 excellent) |
| Max Drawdown | Worst peak-to-trough loss |
| VaR (95%) | Maximum expected daily loss |
| Support/Resistance | Key price levels where reversals occur |
| RFM / R:R | Risk-Reward ratio for trade planning |

---

## 📝 Resume Bullet Points

> *"Built a full-stack Stock Market Analytics Dashboard using Python (yfinance, pandas, Plotly, Streamlit) with 8 feature tabs — real-time technical analysis (RSI, MACD, Bollinger Bands), candlestick pattern recognition (8 patterns), fundamental analysis (P/E, EPS, Analyst targets), risk metrics (Sharpe, VaR, Max Drawdown), benchmark comparison vs NIFTY/S&P500, news sentiment analysis, and portfolio P&L tracker with CSV/Excel export."*

---

## 📸 Screenshots

> _(Add screenshots of your dashboard here)_

---

## ⚠️ Disclaimer

This dashboard is built for **educational purposes only**.
Not financial advice. Always do your own research before investing.

---

*Data source: Yahoo Finance via yfinance · Built by Prashant Meshram*
