"""
Step 2: EDA + Technical Indicators
====================================
- Data cleaning
- Daily returns, volatility
- Moving Averages (20, 50 day)
- RSI (Relative Strength Index)
- Bollinger Bands
- MACD
- Save clean data + charts
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import warnings, os
warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_PATH   = r"C:\Users\DELL\stock_analytics\data\stocks_raw.csv"
CLEAN_PATH  = r"C:\Users\DELL\stock_analytics\data\stocks_clean.csv"
OUTPUT_PATH = r"C:\Users\DELL\stock_analytics\outputs"
os.makedirs(OUTPUT_PATH, exist_ok=True)

# ── Theme ─────────────────────────────────────────────────────────────────────
BG      = "#0F0F1A"
SURFACE = "#1A1A2E"
TEXT    = "#E0E0FF"
MUTED   = "#8888AA"
PALETTE = ["#6C5CE7","#00CEC9","#FDCB6E","#E17055","#55EFC4","#74B9FF","#FD79A8","#A29BFE"]

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": SURFACE,
    "axes.edgecolor": "#2A2A3E", "axes.labelcolor": TEXT,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": TEXT, "grid.color": "#2A2A3E",
    "grid.linestyle": "--", "grid.alpha": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
})

print("=" * 60)
print("  STEP 2 — EDA + TECHNICAL INDICATORS")
print("=" * 60)

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, parse_dates=["Date"])
print(f"\n[1/7] Loaded: {df.shape[0]:,} rows × {df.shape[1]} cols")

# ── Clean ─────────────────────────────────────────────────────────────────────
df.dropna(subset=["Close","Open","High","Low"], inplace=True)
df = df[df["Close"] > 0].copy()
df.sort_values(["Ticker","Date"], inplace=True)
df.reset_index(drop=True, inplace=True)
print(f"[2/7] After cleaning: {df.shape[0]:,} rows")

# ── Feature Engineering ───────────────────────────────────────────────────────
print("[3/7] Calculating features...")

tickers = df["Ticker"].unique()
frames  = []

for ticker in tickers:
    t = df[df["Ticker"] == ticker].copy().reset_index(drop=True)

    # Daily return
    t["Daily_Return"]    = t["Close"].pct_change() * 100

    # Cumulative return
    t["Cumulative_Return"] = ((t["Close"] / t["Close"].iloc[0]) - 1) * 100

    # Moving averages
    t["MA_20"]  = t["Close"].rolling(20).mean()
    t["MA_50"]  = t["Close"].rolling(50).mean()
    t["MA_200"] = t["Close"].rolling(200).mean()

    # Volatility (20-day rolling std)
    t["Volatility_20"] = t["Daily_Return"].rolling(20).std()

    # Bollinger Bands
    t["BB_Mid"]   = t["Close"].rolling(20).mean()
    t["BB_Std"]   = t["Close"].rolling(20).std()
    t["BB_Upper"] = t["BB_Mid"] + 2 * t["BB_Std"]
    t["BB_Lower"] = t["BB_Mid"] - 2 * t["BB_Std"]
    t["BB_Width"] = (t["BB_Upper"] - t["BB_Lower"]) / t["BB_Mid"] * 100

    # RSI (14-day)
    delta = t["Close"].diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs        = avg_gain / avg_loss.replace(0, np.nan)
    t["RSI"]  = 100 - (100 / (1 + rs))

    # MACD
    ema12      = t["Close"].ewm(span=12, adjust=False).mean()
    ema26      = t["Close"].ewm(span=26, adjust=False).mean()
    t["MACD"]  = ema12 - ema26
    t["MACD_Signal"] = t["MACD"].ewm(span=9, adjust=False).mean()
    t["MACD_Hist"]   = t["MACD"] - t["MACD_Signal"]

    # Price position in 52-week range
    t["52W_High"] = t["Close"].rolling(252).max()
    t["52W_Low"]  = t["Close"].rolling(252).min()
    t["52W_Pct"]  = (t["Close"] - t["52W_Low"]) / (t["52W_High"] - t["52W_Low"] + 1e-6) * 100

    frames.append(t)

df = pd.concat(frames, ignore_index=True)
df.to_csv(CLEAN_PATH, index=False)
print(f"[4/7] Clean data saved → {CLEAN_PATH}")
print(f"      Columns: {df.shape[1]}")

# ── Quick Stats ───────────────────────────────────────────────────────────────
print("\n── Performance Summary ─────────────────────────────────")
summary = (df.groupby("Company")
             .agg(
                 Latest_Close  = ("Close", "last"),
                 Total_Return  = ("Cumulative_Return", "last"),
                 Avg_Volatility= ("Volatility_20", "mean"),
                 Avg_RSI       = ("RSI", "mean"),
             )
             .round(2)
             .sort_values("Total_Return", ascending=False))
print(summary.to_string())

# ════════════════════════════════════════════════════════════════════════════
# CHARTS
# ════════════════════════════════════════════════════════════════════════════

# ── Chart 1: Price Trend — All Stocks ────────────────────────────────────────
print("\n[5/7] Generating charts...")
fig, axes = plt.subplots(2, 4, figsize=(20, 8), facecolor=BG)
axes = axes.flatten()

for i, (ticker, color) in enumerate(zip(tickers, PALETTE)):
    t   = df[df["Ticker"] == ticker]
    ax  = axes[i]
    ax.set_facecolor(SURFACE)
    ax.plot(t["Date"], t["Close"], color=color, linewidth=1.5, label="Close")
    ax.plot(t["Date"], t["MA_20"], color="white", linewidth=0.8, alpha=0.5, linestyle="--", label="MA20")
    ax.plot(t["Date"], t["MA_50"], color=MUTED,   linewidth=0.8, alpha=0.5, linestyle=":",  label="MA50")
    ax.fill_between(t["Date"], t["BB_Lower"], t["BB_Upper"], alpha=0.06, color=color)
    ax.set_title(t["Company"].iloc[0], color=TEXT, fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=7)
    ax.grid(True)
    name = t["Company"].iloc[0]
    ret  = t["Cumulative_Return"].iloc[-1]
    col  = "#55EFC4" if ret >= 0 else "#E17055"
    ax.annotate(f"{ret:+.1f}%", xy=(0.98, 0.05), xycoords="axes fraction",
                ha="right", fontsize=9, color=col, fontweight="bold")

plt.suptitle("Stock Price Trends with Moving Averages & Bollinger Bands",
             color=TEXT, fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(f"{OUTPUT_PATH}/01_price_trends.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("  ✅ Chart 1: Price Trends saved")

# ── Chart 2: Cumulative Returns Comparison ────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 6), facecolor=BG)
ax.set_facecolor(SURFACE)
ax.axhline(0, color=MUTED, linewidth=0.8, linestyle="--")

for i, ticker in enumerate(tickers):
    t = df[df["Ticker"] == ticker]
    ax.plot(t["Date"], t["Cumulative_Return"],
            color=PALETTE[i], linewidth=2,
            label=t["Company"].iloc[0])
    last_ret = t["Cumulative_Return"].iloc[-1]
    ax.annotate(f"{last_ret:+.1f}%",
                xy=(t["Date"].iloc[-1], last_ret),
                xytext=(5, 0), textcoords="offset points",
                color=PALETTE[i], fontsize=8, fontweight="bold")

ax.set_title("Cumulative Returns Comparison (2 Years)", color=TEXT, fontsize=14, fontweight="bold")
ax.set_ylabel("Cumulative Return (%)", color=MUTED)
ax.legend(loc="upper left", fontsize=8, framealpha=0.3)
ax.grid(True)
plt.tight_layout()
plt.savefig(f"{OUTPUT_PATH}/02_cumulative_returns.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("  ✅ Chart 2: Cumulative Returns saved")

# ── Chart 3: Correlation Heatmap ──────────────────────────────────────────────
pivot = df.pivot_table(index="Date", columns="Company", values="Daily_Return")
corr  = pivot.corr()

fig, ax = plt.subplots(figsize=(10, 8), facecolor=BG)
ax.set_facecolor(SURFACE)
sns.heatmap(corr, ax=ax, cmap="RdYlGn", center=0, annot=True, fmt=".2f",
            linewidths=0.5, linecolor=BG, annot_kws={"size": 9},
            cbar_kws={"shrink": 0.8})
ax.set_title("Stock Returns Correlation Matrix", color=TEXT, fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUTPUT_PATH}/03_correlation.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("  ✅ Chart 3: Correlation Heatmap saved")

# ── Chart 4: RSI Panel ────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 4, figsize=(20, 6), facecolor=BG)
axes = axes.flatten()

for i, (ticker, color) in enumerate(zip(tickers, PALETTE)):
    t  = df[df["Ticker"] == ticker].dropna(subset=["RSI"])
    ax = axes[i]
    ax.set_facecolor(SURFACE)
    ax.plot(t["Date"], t["RSI"], color=color, linewidth=1.5)
    ax.axhline(70, color="#E17055", linewidth=0.8, linestyle="--", alpha=0.7)
    ax.axhline(30, color="#55EFC4", linewidth=0.8, linestyle="--", alpha=0.7)
    ax.fill_between(t["Date"], t["RSI"], 70,
                    where=(t["RSI"] >= 70), alpha=0.2, color="#E17055", label="Overbought")
    ax.fill_between(t["Date"], t["RSI"], 30,
                    where=(t["RSI"] <= 30), alpha=0.2, color="#55EFC4", label="Oversold")
    ax.set_ylim(0, 100)
    ax.set_title(t["Company"].iloc[0], color=TEXT, fontsize=9, fontweight="bold")
    ax.tick_params(labelsize=7)
    ax.grid(True)

plt.suptitle("RSI — Relative Strength Index (Overbought > 70 | Oversold < 30)",
             color=TEXT, fontsize=13, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(f"{OUTPUT_PATH}/04_rsi.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("  ✅ Chart 4: RSI saved")

# ── Chart 5: Volatility Comparison ───────────────────────────────────────────
vol = (df.groupby("Company")["Volatility_20"].mean()
         .sort_values(ascending=False).reset_index())

fig, ax = plt.subplots(figsize=(12, 5), facecolor=BG)
ax.set_facecolor(SURFACE)
bars = ax.barh(vol["Company"], vol["Volatility_20"],
               color=PALETTE[:len(vol)], height=0.6)
ax.set_title("Average 20-Day Volatility by Stock", color=TEXT, fontsize=13, fontweight="bold")
ax.set_xlabel("Volatility (%)", color=MUTED)
ax.grid(axis="x")
for bar, val in zip(bars, vol["Volatility_20"]):
    ax.text(val + 0.02, bar.get_y() + bar.get_height()/2,
            f"{val:.2f}%", va="center", fontsize=9, color=MUTED)
plt.tight_layout()
plt.savefig(f"{OUTPUT_PATH}/05_volatility.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close()
print("  ✅ Chart 5: Volatility saved")

print(f"\n[7/7] All charts saved → {OUTPUT_PATH}")
print("\n" + "=" * 60)
print("  EDA COMPLETE!")
print("=" * 60)