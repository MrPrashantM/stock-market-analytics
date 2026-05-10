"""
Step 3: Stock Market Analytics Dashboard
==========================================
Streamlit + Plotly interactive dashboard:
  - Stock price with candlestick chart
  - Technical indicators (MA, RSI, MACD, Bollinger Bands)
  - Multi-stock comparison
  - Portfolio tracker
  - Correlation heatmap
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0a0a12; }

    section[data-testid="stSidebar"] {
        background: #111120 !important;
        border-right: 1px solid #2a2a3e;
    }

    .kpi-card {
        background: #16162a;
        border: 1px solid #2a2a3e;
        border-radius: 12px;
        padding: 18px 22px;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 12px 12px 0 0;
    }
    .kpi-card.purple::before { background: #6c5ce7; }
    .kpi-card.green::before  { background: #22c55e; }
    .kpi-card.red::before    { background: #ef4444; }
    .kpi-card.teal::before   { background: #00cec9; }
    .kpi-card.orange::before { background: #f97316; }

    .kpi-label {
        font-size: 0.68rem;
        color: #6666aa;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 500;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-family: 'Space Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        line-height: 1;
    }
    .kpi-sub { font-size: 0.72rem; color: #6666aa; margin-top: 4px; }
    .kpi-card.purple .kpi-value { color: #a78bfa; }
    .kpi-card.green  .kpi-value { color: #4ade80; }
    .kpi-card.red    .kpi-value { color: #f87171; }
    .kpi-card.teal   .kpi-value { color: #2dd4bf; }
    .kpi-card.orange .kpi-value { color: #fb923c; }

    .section-header {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: #6666aa;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        border-bottom: 1px solid #2a2a3e;
        padding-bottom: 8px;
        margin-bottom: 16px;
        margin-top: 8px;
    }

    .signal-box {
        background: #16162a;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        font-size: 0.82rem;
        color: #aaaacc;
    }
    .signal-box strong { color: #e0e0ff; }

    h1, h2, h3 { color: #e0e0ff !important; }
    .stSelectbox label, .stMultiSelect label { color: #8888bb !important; font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Plotly Theme ──────────────────────────────────────────────────────────────
LAYOUT = dict(
    plot_bgcolor  = "#16162a",
    paper_bgcolor = "#16162a",
    font_color    = "#aaaacc",
    font_family   = "Inter",
    title_font_color = "#e0e0ff",
    title_font_size  = 14,
    margin = dict(l=10, r=10, t=40, b=10),
    xaxis  = dict(gridcolor="#2a2a3e", linecolor="#2a2a3e", showgrid=True),
    yaxis  = dict(gridcolor="#2a2a3e", linecolor="#2a2a3e", showgrid=True),
)

PALETTE = ["#6c5ce7","#00cec9","#f97316","#22c55e","#ef4444","#ec4899","#f59e0b","#3b82f6"]

def apply_layout(fig, **kwargs):
    fig.update_layout(**LAYOUT, **kwargs)
    return fig

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(
        r"C:\Users\DELL\stock_analytics\data\stocks_clean.csv",
        parse_dates=["Date"]
    )
    return df

df_full = load_data()

companies  = sorted(df_full["Company"].unique())
company_to_ticker = df_full[["Company","Ticker"]].drop_duplicates().set_index("Company")["Ticker"].to_dict()

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("# 📈 Stock Analytics")
    st.markdown("**Real Market Data · 2Y**")
    st.divider()

    page = st.radio("Navigation", [
        "📊 Stock Analysis",
        "🔄 Compare Stocks",
        "💼 Portfolio Tracker",
        "🔥 Heatmap & Correlation",
    ])

    st.divider()

    selected_company = st.selectbox("Select Stock", companies)
    selected_ticker  = company_to_ticker[selected_company]

    date_range = st.date_input(
        "Date Range",
        value=[df_full["Date"].min(), df_full["Date"].max()],
        min_value=df_full["Date"].min(),
        max_value=df_full["Date"].max(),
    )

    st.divider()
    st.caption("Data: Yahoo Finance · yfinance\nCharts: Plotly · Streamlit")

# ── Filter ────────────────────────────────────────────────────────────────────
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start = df_full["Date"].min()
    end   = df_full["Date"].max()

df_stock = df_full[
    (df_full["Company"] == selected_company) &
    (df_full["Date"] >= start) &
    (df_full["Date"] <= end)
].copy()

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — STOCK ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
if page == "📊 Stock Analysis":

    st.markdown(f"## {selected_company} `{selected_ticker}`")

    # KPIs
    latest      = df_stock["Close"].iloc[-1]
    prev        = df_stock["Close"].iloc[-2]
    day_chg     = ((latest - prev) / prev * 100)
    total_ret   = df_stock["Cumulative_Return"].iloc[-1]
    avg_vol     = df_stock["Volatility_20"].mean()
    latest_rsi  = df_stock["RSI"].iloc[-1]
    high_52w    = df_stock["52W_High"].iloc[-1]
    low_52w     = df_stock["52W_Low"].iloc[-1]

    k1,k2,k3,k4,k5 = st.columns(5)

    price_color = "green" if day_chg >= 0 else "red"
    ret_color   = "green" if total_ret >= 0 else "red"

    with k1:
        st.markdown(f"""<div class="kpi-card purple">
            <div class="kpi-label">Current Price</div>
            <div class="kpi-value">{latest:.2f}</div>
            <div class="kpi-sub">{selected_ticker}</div>
        </div>""", unsafe_allow_html=True)

    with k2:
        arrow = "▲" if day_chg >= 0 else "▼"
        st.markdown(f"""<div class="kpi-card {price_color}">
            <div class="kpi-label">Day Change</div>
            <div class="kpi-value">{arrow} {abs(day_chg):.2f}%</div>
            <div class="kpi-sub">vs previous close</div>
        </div>""", unsafe_allow_html=True)

    with k3:
        arrow2 = "▲" if total_ret >= 0 else "▼"
        st.markdown(f"""<div class="kpi-card {ret_color}">
            <div class="kpi-label">Total Return</div>
            <div class="kpi-value">{arrow2} {abs(total_ret):.1f}%</div>
            <div class="kpi-sub">Since start of period</div>
        </div>""", unsafe_allow_html=True)

    with k4:
        rsi_color = "red" if latest_rsi > 70 else "green" if latest_rsi < 30 else "teal"
        rsi_label = "Overbought" if latest_rsi > 70 else "Oversold" if latest_rsi < 30 else "Neutral"
        st.markdown(f"""<div class="kpi-card {rsi_color}">
            <div class="kpi-label">RSI (14)</div>
            <div class="kpi-value">{latest_rsi:.1f}</div>
            <div class="kpi-sub">{rsi_label}</div>
        </div>""", unsafe_allow_html=True)

    with k5:
        st.markdown(f"""<div class="kpi-card orange">
            <div class="kpi-label">Volatility (20D)</div>
            <div class="kpi-value">{avg_vol:.2f}%</div>
            <div class="kpi-sub">Avg daily std dev</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Candlestick + Volume ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Price Chart with Technical Indicators</div>', unsafe_allow_html=True)

    show_ma   = st.checkbox("Moving Averages (20/50/200)", value=True)
    show_bb   = st.checkbox("Bollinger Bands", value=True)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.2, 0.2],
                        vertical_spacing=0.03)

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_stock["Date"],
        open=df_stock["Open"], high=df_stock["High"],
        low=df_stock["Low"],   close=df_stock["Close"],
        increasing_line_color="#22c55e",
        decreasing_line_color="#ef4444",
        name="Price",
    ), row=1, col=1)

    if show_ma:
        for ma, color, width in [("MA_20","#f59e0b",1.5),("MA_50","#6c5ce7",1.5),("MA_200","#ec4899",1)]:
            fig.add_trace(go.Scatter(
                x=df_stock["Date"], y=df_stock[ma],
                line=dict(color=color, width=width),
                name=ma.replace("_"," "), opacity=0.8,
            ), row=1, col=1)

    if show_bb:
        fig.add_trace(go.Scatter(
            x=df_stock["Date"], y=df_stock["BB_Upper"],
            line=dict(color="#aaaacc", width=0.8, dash="dash"),
            name="BB Upper", opacity=0.5,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_stock["Date"], y=df_stock["BB_Lower"],
            line=dict(color="#aaaacc", width=0.8, dash="dash"),
            name="BB Lower", opacity=0.5,
            fill="tonexty", fillcolor="rgba(170,170,204,0.05)",
        ), row=1, col=1)

    # Volume
    colors_vol = ["#22c55e" if c >= o else "#ef4444"
                  for c, o in zip(df_stock["Close"], df_stock["Open"])]
    fig.add_trace(go.Bar(
        x=df_stock["Date"], y=df_stock["Volume"],
        marker_color=colors_vol, name="Volume", opacity=0.7,
    ), row=2, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=df_stock["Date"], y=df_stock["RSI"],
        line=dict(color="#6c5ce7", width=1.5), name="RSI",
    ), row=3, col=1)
    fig.add_hline(y=70, line_color="#ef4444", line_dash="dash", line_width=0.8, row=3, col=1)
    fig.add_hline(y=30, line_color="#22c55e", line_dash="dash", line_width=0.8, row=3, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="#ef4444", opacity=0.05, row=3, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="#22c55e", opacity=0.05, row=3, col=1)

    fig.update_layout(
        **{k:v for k,v in LAYOUT.items() if k not in ["xaxis","yaxis"]},
        height=600, showlegend=True,
        xaxis_rangeslider_visible=False,
        legend=dict(bgcolor="#1e1e35", bordercolor="#2a2a3e", font_size=10),
    )
    fig.update_xaxes(gridcolor="#2a2a3e", linecolor="#2a2a3e")
    fig.update_yaxes(gridcolor="#2a2a3e", linecolor="#2a2a3e")
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0,100])

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── MACD ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📉 MACD — Moving Average Convergence Divergence</div>', unsafe_allow_html=True)

    fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         row_heights=[0.6, 0.4], vertical_spacing=0.05)

    fig2.add_trace(go.Scatter(
        x=df_stock["Date"], y=df_stock["MACD"],
        line=dict(color="#6c5ce7", width=1.5), name="MACD",
    ), row=1, col=1)
    fig2.add_trace(go.Scatter(
        x=df_stock["Date"], y=df_stock["MACD_Signal"],
        line=dict(color="#f59e0b", width=1.5), name="Signal",
    ), row=1, col=1)

    colors_macd = ["#22c55e" if v >= 0 else "#ef4444" for v in df_stock["MACD_Hist"]]
    fig2.add_trace(go.Bar(
        x=df_stock["Date"], y=df_stock["MACD_Hist"],
        marker_color=colors_macd, name="Histogram", opacity=0.7,
    ), row=2, col=1)

    fig2.update_layout(
        **{k:v for k,v in LAYOUT.items() if k not in ["xaxis","yaxis"]},
        height=350,
        legend=dict(bgcolor="#1e1e35", bordercolor="#2a2a3e", font_size=10),
    )
    fig2.update_xaxes(gridcolor="#2a2a3e", linecolor="#2a2a3e")
    fig2.update_yaxes(gridcolor="#2a2a3e", linecolor="#2a2a3e")
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # ── Trading Signals ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">💡 Trading Signals</div>', unsafe_allow_html=True)

    latest_macd   = df_stock["MACD"].iloc[-1]
    latest_signal = df_stock["MACD_Signal"].iloc[-1]
    latest_ma20   = df_stock["MA_20"].iloc[-1]
    latest_ma50   = df_stock["MA_50"].iloc[-1]
    latest_close  = df_stock["Close"].iloc[-1]
    bb_upper      = df_stock["BB_Upper"].iloc[-1]
    bb_lower      = df_stock["BB_Lower"].iloc[-1]

    signals = []
    if latest_rsi > 70:
        signals.append(("🔴", "RSI Overbought", f"RSI = {latest_rsi:.1f} — Stock may be overvalued. Consider selling."))
    elif latest_rsi < 30:
        signals.append(("🟢", "RSI Oversold", f"RSI = {latest_rsi:.1f} — Stock may be undervalued. Consider buying."))
    else:
        signals.append(("🟡", "RSI Neutral", f"RSI = {latest_rsi:.1f} — No strong signal."))

    if latest_macd > latest_signal:
        signals.append(("🟢", "MACD Bullish", "MACD line above signal — Bullish momentum."))
    else:
        signals.append(("🔴", "MACD Bearish", "MACD line below signal — Bearish momentum."))

    if latest_ma20 > latest_ma50:
        signals.append(("🟢", "Golden Cross", "MA20 above MA50 — Uptrend confirmed."))
    else:
        signals.append(("🔴", "Death Cross", "MA20 below MA50 — Downtrend signal."))

    if latest_close > bb_upper:
        signals.append(("🔴", "Above Bollinger Upper Band", "Price above upper band — Potential reversal."))
    elif latest_close < bb_lower:
        signals.append(("🟢", "Below Bollinger Lower Band", "Price below lower band — Potential bounce."))
    else:
        signals.append(("🟡", "Inside Bollinger Bands", "Price within normal range."))

    c1, c2 = st.columns(2)
    for i, (emoji, title, desc) in enumerate(signals):
        col = c1 if i % 2 == 0 else c2
        with col:
            st.markdown(f"""<div class="signal-box">
                {emoji} <strong>{title}</strong><br>{desc}
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — COMPARE STOCKS
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔄 Compare Stocks":
    st.markdown("## Stock Comparison")

    selected_stocks = st.multiselect(
        "Select stocks to compare",
        options=companies,
        default=companies[:4],
    )

    if not selected_stocks:
        st.warning("Please select at least one stock.")
        st.stop()

    df_compare = df_full[
        (df_full["Company"].isin(selected_stocks)) &
        (df_full["Date"] >= start) &
        (df_full["Date"] <= end)
    ]

    # Cumulative Returns
    st.markdown('<div class="section-header">📈 Cumulative Returns</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for i, company in enumerate(selected_stocks):
        t = df_compare[df_compare["Company"] == company]
        ret = t["Cumulative_Return"].iloc[-1]
        fig.add_trace(go.Scatter(
            x=t["Date"], y=t["Cumulative_Return"],
            name=f"{company} ({ret:+.1f}%)",
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
        ))
    fig.add_hline(y=0, line_color="#6666aa", line_dash="dash", line_width=0.8)
    apply_layout(fig, title="Cumulative Returns (%)", height=400)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Performance Table
    st.markdown('<div class="section-header">📋 Performance Metrics</div>', unsafe_allow_html=True)
    perf = []
    for company in selected_stocks:
        t = df_compare[df_compare["Company"] == company]
        if len(t) < 2: continue
        perf.append({
            "Company":       company,
            "Current Price": f"{t['Close'].iloc[-1]:.2f}",
            "Total Return":  f"{t['Cumulative_Return'].iloc[-1]:+.1f}%",
            "Volatility":    f"{t['Volatility_20'].mean():.2f}%",
            "Avg RSI":       f"{t['RSI'].mean():.1f}",
            "52W High":      f"{t['52W_High'].iloc[-1]:.2f}",
            "52W Low":       f"{t['52W_Low'].iloc[-1]:.2f}",
        })
    st.dataframe(pd.DataFrame(perf), use_container_width=True, hide_index=True)

    # Volatility comparison
    st.markdown('<div class="section-header">📉 Volatility Over Time</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    for i, company in enumerate(selected_stocks):
        t = df_compare[df_compare["Company"] == company].dropna(subset=["Volatility_20"])
        fig2.add_trace(go.Scatter(
            x=t["Date"], y=t["Volatility_20"],
            name=company,
            line=dict(color=PALETTE[i % len(PALETTE)], width=1.5),
        ))
    apply_layout(fig2, title="20-Day Rolling Volatility (%)", height=350)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PORTFOLIO TRACKER
# ════════════════════════════════════════════════════════════════════════════
elif page == "💼 Portfolio Tracker":
    st.markdown("## Portfolio Tracker")
    st.caption("Enter your holdings to calculate portfolio value and returns")

    st.markdown('<div class="section-header">📥 Enter Holdings</div>', unsafe_allow_html=True)

    holdings = {}
    cols = st.columns(4)
    for i, company in enumerate(companies):
        with cols[i % 4]:
            qty = st.number_input(f"{company[:15]}", min_value=0, value=0, step=1, key=company)
            if qty > 0:
                holdings[company] = qty

    if not holdings:
        st.info("Enter quantity for at least one stock above.")
        st.stop()

    # Calculate portfolio
    portfolio_rows = []
    total_value    = 0
    total_invested = 0

    for company, qty in holdings.items():
        t = df_full[df_full["Company"] == company]
        buy_price  = t["Close"].iloc[0]
        curr_price = t["Close"].iloc[-1]
        curr_val   = curr_price * qty
        invested   = buy_price  * qty
        pnl        = curr_val - invested
        pnl_pct    = (pnl / invested * 100) if invested > 0 else 0

        total_value    += curr_val
        total_invested += invested

        portfolio_rows.append({
            "Company":       company,
            "Qty":           qty,
            "Buy Price":     round(buy_price, 2),
            "Current Price": round(curr_price, 2),
            "Invested":      round(invested, 2),
            "Current Value": round(curr_val, 2),
            "P&L":           round(pnl, 2),
            "P&L %":         round(pnl_pct, 2),
        })

    total_pnl     = total_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    pnl_col = "green" if total_pnl >= 0 else "red"
    arrow   = "▲" if total_pnl >= 0 else "▼"

    with k1:
        st.markdown(f"""<div class="kpi-card purple">
            <div class="kpi-label">Total Invested</div>
            <div class="kpi-value">{total_invested:,.0f}</div>
            <div class="kpi-sub">Initial investment</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card teal">
            <div class="kpi-label">Current Value</div>
            <div class="kpi-value">{total_value:,.0f}</div>
            <div class="kpi-sub">Market value today</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-card {pnl_col}">
            <div class="kpi-label">Total P&L</div>
            <div class="kpi-value">{arrow} {abs(total_pnl):,.0f}</div>
            <div class="kpi-sub">Profit / Loss</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card {pnl_col}">
            <div class="kpi-label">Return %</div>
            <div class="kpi-value">{arrow} {abs(total_pnl_pct):.1f}%</div>
            <div class="kpi-sub">Overall return</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Holdings table
    df_port = pd.DataFrame(portfolio_rows)
    st.dataframe(df_port, use_container_width=True, hide_index=True)

    # Allocation pie
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Pie(
            labels=df_port["Company"],
            values=df_port["Current Value"],
            hole=0.6,
            marker_colors=PALETTE[:len(df_port)],
            hovertemplate="<b>%{label}</b><br>Value: %{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig.update_layout(**{k:v for k,v in LAYOUT.items() if k not in ["xaxis","yaxis"]},
                          title="Portfolio Allocation", height=350, showlegend=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        colors_pnl = ["#22c55e" if v >= 0 else "#ef4444" for v in df_port["P&L"]]
        fig2 = go.Figure(go.Bar(
            x=df_port["Company"], y=df_port["P&L %"],
            marker_color=colors_pnl,
            text=[f"{v:+.1f}%" for v in df_port["P&L %"]],
            textposition="outside",
        ))
        fig2.add_hline(y=0, line_color="#6666aa", line_width=0.8)
        apply_layout(fig2, title="P&L % by Stock", height=350)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — HEATMAP & CORRELATION
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔥 Heatmap & Correlation":
    st.markdown("## Heatmap & Correlation Analysis")

    # Correlation matrix
    st.markdown('<div class="section-header">🔗 Returns Correlation Matrix</div>', unsafe_allow_html=True)
    pivot = df_full[df_full["Date"].between(start, end)].pivot_table(
        index="Date", columns="Company", values="Daily_Return"
    )
    corr = pivot.corr().round(2)

    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
        colorscale="RdYlGn", zmid=0,
        text=corr.values, texttemplate="%{text:.2f}", textfont_size=10,
        hoverongaps=False,
        hovertemplate="<b>%{x} × %{y}</b><br>Correlation: %{z:.2f}<extra></extra>",
        colorbar=dict(tickfont_color="#aaaacc"),
    ))
    apply_layout(fig, title="Daily Returns Correlation", height=450)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Monthly return heatmap
    st.markdown('<div class="section-header">📅 Monthly Returns Heatmap</div>', unsafe_allow_html=True)

    df_monthly = df_full[df_full["Company"] == selected_company].copy()
    df_monthly["Month"] = df_monthly["Date"].dt.to_period("M").astype(str)
    monthly_ret = df_monthly.groupby("Month")["Daily_Return"].sum().reset_index()
    monthly_ret["Year"]  = monthly_ret["Month"].str[:4]
    monthly_ret["Month_Name"] = pd.to_datetime(monthly_ret["Month"]).dt.strftime("%b")

    pivot_m = monthly_ret.pivot_table(index="Year", columns="Month_Name", values="Daily_Return")
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    pivot_m = pivot_m.reindex(columns=[m for m in month_order if m in pivot_m.columns])

    fig2 = go.Figure(go.Heatmap(
        z=pivot_m.values, x=pivot_m.columns.tolist(), y=pivot_m.index.tolist(),
        colorscale="RdYlGn", zmid=0,
        text=np.round(pivot_m.values, 1),
        texttemplate="%{text:.1f}%", textfont_size=10,
        hovertemplate="<b>%{y} %{x}</b><br>Return: %{z:.2f}%<extra></extra>",
        colorbar=dict(tickfont_color="#aaaacc"),
    ))
    apply_layout(fig2, title=f"Monthly Returns — {selected_company}", height=200)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Insight
    st.markdown('<div class="section-header">💡 Correlation Insights</div>', unsafe_allow_html=True)
    high_corr = []
    for i in range(len(corr.columns)):
        for j in range(i+1, len(corr.columns)):
            val = corr.iloc[i, j]
            if abs(val) > 0.6:
                high_corr.append((corr.columns[i], corr.columns[j], val))

    if high_corr:
        for s1, s2, val in sorted(high_corr, key=lambda x: -abs(x[2]))[:4]:
            color = "#22c55e" if val > 0 else "#ef4444"
            direction = "move together" if val > 0 else "move opposite"
            st.markdown(f"""<div class="signal-box">
                <strong style="color:{color}">{s1} ↔ {s2}: {val:.2f}</strong><br>
                These stocks tend to {direction} — correlation of {val:.2f}
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No strong correlations (>0.6) found in selected date range.")

st.divider()
st.caption("📈 Stock Market Analytics · yfinance · Plotly · Streamlit · Portfolio Project 2024")
