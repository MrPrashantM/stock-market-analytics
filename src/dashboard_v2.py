"""
Stock Market Analytics Dashboard — Premium Edition
====================================================
- Search ANY stock (NSE/BSE/US) live via yfinance
- Full technical analysis: Candlestick, RSI, MACD, Bollinger Bands
- Multi-stock comparison
- Portfolio tracker
- Classy dark UI — Bloomberg terminal inspired
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import warnings, datetime
warnings.filterwarnings("ignore")

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarketLens — Stock Analytics",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS — Bloomberg Terminal + Luxury Dark ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background: #080810;
}

.stApp { background: #080810; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0c0c18 !important;
    border-right: 1px solid #1e1e3a;
}
section[data-testid="stSidebar"] * { color: #9999cc !important; }
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] .big-title { color: #e0e0ff !important; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* KPI Cards */
.kpi-row { display: flex; gap: 12px; margin-bottom: 20px; }

.kpi {
    flex: 1;
    background: #0e0e1e;
    border: 1px solid #1e1e3a;
    border-top: 2px solid;
    padding: 16px 20px;
    font-family: 'IBM Plex Mono', monospace;
    position: relative;
    overflow: hidden;
}
.kpi::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 40px; height: 40px;
    background: currentColor;
    opacity: 0.03;
    clip-path: polygon(100% 0, 0 0, 100% 100%);
}
.kpi.up   { border-top-color: #00ff88; }
.kpi.down { border-top-color: #ff4466; }
.kpi.neu  { border-top-color: #4466ff; }
.kpi.warn { border-top-color: #ffaa00; }

.kpi-label {
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    color: #444466;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.kpi-val {
    font-size: 1.4rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1;
}
.kpi.up   .kpi-val { color: #00ff88; }
.kpi.down .kpi-val { color: #ff4466; }
.kpi.neu  .kpi-val { color: #6688ff; }
.kpi.warn .kpi-val { color: #ffaa00; }
.kpi-sub {
    font-size: 0.65rem;
    color: #333355;
    margin-top: 4px;
    letter-spacing: 0.05em;
}

/* Section label */
.sec-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.25em;
    color: #333355;
    text-transform: uppercase;
    border-left: 2px solid #4466ff;
    padding-left: 10px;
    margin: 24px 0 14px;
}

/* Signal cards */
.sig {
    background: #0e0e1e;
    border: 1px solid #1e1e3a;
    border-left: 3px solid;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #7777aa;
    line-height: 1.6;
}
.sig.bull { border-left-color: #00ff88; }
.sig.bear { border-left-color: #ff4466; }
.sig.neut { border-left-color: #4466ff; }
.sig strong { color: #ccccee; }

/* Ticker badge */
.ticker-badge {
    display: inline-block;
    background: #1a1a30;
    border: 1px solid #4466ff;
    color: #4466ff;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    padding: 3px 10px;
    letter-spacing: 0.1em;
    margin-left: 10px;
    vertical-align: middle;
}

/* Header */
.main-header {
    border-bottom: 1px solid #1e1e3a;
    padding-bottom: 16px;
    margin-bottom: 20px;
}
.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #e0e0ff;
    letter-spacing: -0.02em;
    line-height: 1;
}
.main-title span { color: #4466ff; }
.main-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #333355;
    letter-spacing: 0.15em;
    margin-top: 4px;
    text-transform: uppercase;
}

/* Input override */
.stTextInput input {
    background: #0e0e1e !important;
    border: 1px solid #2a2a4a !important;
    color: #e0e0ff !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.9rem !important;
    border-radius: 0 !important;
}
.stTextInput input:focus {
    border-color: #4466ff !important;
    box-shadow: 0 0 0 1px #4466ff !important;
}

.stSelectbox > div > div {
    background: #0e0e1e !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 0 !important;
    color: #e0e0ff !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #1e1e3a;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #444466;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #4466ff !important;
    border-bottom-color: #4466ff !important;
    background: transparent !important;
}

/* Table */
.stDataFrame { border: 1px solid #1e1e3a; }
</style>
""", unsafe_allow_html=True)

# ── Plotly Theme ──────────────────────────────────────────────────────────────
BG      = "#080810"
SURFACE = "#0e0e1e"
GRID    = "#16162a"
TEXT    = "#9999cc"
ACCENT  = "#4466ff"
GREEN   = "#00ff88"
RED     = "#ff4466"
AMBER   = "#ffaa00"
PALETTE = [ACCENT,"#aa44ff","#00ccff",GREEN,RED,AMBER,"#ff44aa","#44ffcc"]

BASE_LAYOUT = dict(
    plot_bgcolor  = SURFACE,
    paper_bgcolor = BG,
    font          = dict(family="IBM Plex Mono", color=TEXT, size=11),
    title_font    = dict(color="#ccccee", size=13, family="Syne"),
    margin        = dict(l=8, r=8, t=36, b=8),
    legend        = dict(bgcolor=SURFACE, bordercolor="#1e1e3a",
                         borderwidth=1, font_size=10),
    xaxis = dict(gridcolor=GRID, linecolor="#1e1e3a", tickcolor=TEXT,
                 showgrid=True, zeroline=False),
    yaxis = dict(gridcolor=GRID, linecolor="#1e1e3a", tickcolor=TEXT,
                 showgrid=True, zeroline=False),
)

def themed(fig, height=400, **kw):
    fig.update_layout(**BASE_LAYOUT, height=height, **kw)
    fig.update_xaxes(gridcolor=GRID, linecolor="#1e1e3a")
    fig.update_yaxes(gridcolor=GRID, linecolor="#1e1e3a")
    return fig

# ── Technical Indicators ──────────────────────────────────────────────────────
def add_indicators(df):
    df = df.copy()
    df["MA20"]   = df["Close"].rolling(20).mean()
    df["MA50"]   = df["Close"].rolling(50).mean()
    df["MA200"]  = df["Close"].rolling(200).mean()
    df["Vol20"]  = df["Close"].pct_change().rolling(20).std() * 100

    df["BB_Mid"]   = df["Close"].rolling(20).mean()
    df["BB_Std"]   = df["Close"].rolling(20).std()
    df["BB_Up"]    = df["BB_Mid"] + 2 * df["BB_Std"]
    df["BB_Lo"]    = df["BB_Mid"] - 2 * df["BB_Std"]

    delta       = df["Close"].diff()
    gain        = delta.clip(lower=0).rolling(14).mean()
    loss        = (-delta.clip(upper=0)).rolling(14).mean()
    df["RSI"]   = 100 - 100 / (1 + gain / loss.replace(0, np.nan))

    ema12        = df["Close"].ewm(span=12, adjust=False).mean()
    ema26        = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]   = ema12 - ema26
    df["MACDs"]  = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACDh"]  = df["MACD"] - df["MACDs"]

    df["Return"] = df["Close"].pct_change() * 100
    df["CumRet"] = (df["Close"] / df["Close"].iloc[0] - 1) * 100
    return df

# ── Fetch Data ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch(ticker, period="1y"):
    try:
        t  = yf.Ticker(ticker)
        df = t.history(period=period)
        if df.empty:
            return None, None
        df = df.reset_index()[["Date","Open","High","Low","Close","Volume"]]
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        info = t.info
        return add_indicators(df), info
    except:
        return None, None

# ── Popular Stocks Quick Select ───────────────────────────────────────────────
QUICK = {
    "🇮🇳 India": {
        "RELIANCE.NS":"Reliance", "TCS.NS":"TCS",
        "HDFCBANK.NS":"HDFC Bank", "INFY.NS":"Infosys",
        "WIPRO.NS":"Wipro", "TATAMOTORS.NS":"Tata Motors",
        "ADANIENT.NS":"Adani Ent.", "BAJFINANCE.NS":"Bajaj Finance",
    },
    "🇺🇸 US": {
        "AAPL":"Apple", "MSFT":"Microsoft",
        "GOOGL":"Google", "AMZN":"Amazon",
        "NVDA":"Nvidia", "TSLA":"Tesla",
        "META":"Meta", "NFLX":"Netflix",
    },
}

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📡 MarketLens")
    st.markdown("---")

    st.markdown("**Search any stock**")
    custom_ticker = st.text_input(
        "", placeholder="e.g. INFY.NS, AAPL, TSLA",
        label_visibility="collapsed"
    ).upper().strip()

    st.markdown("**Or pick a popular stock**")
    market = st.selectbox("Market", list(QUICK.keys()), label_visibility="collapsed")
    picked = st.selectbox(
        "Stock", list(QUICK[market].values()),
        label_visibility="collapsed"
    )
    picked_ticker = {v: k for k, v in QUICK[market].items()}[picked]

    ticker = custom_ticker if custom_ticker else picked_ticker

    st.markdown("---")
    period = st.select_slider(
        "Period",
        options=["1mo","3mo","6mo","1y","2y","5y"],
        value="1y"
    )

    st.markdown("---")
    st.markdown(f"""
    <div style='font-family: IBM Plex Mono; font-size: 0.6rem; color: #222244; letter-spacing: 0.1em;'>
    ACTIVE TICKER<br>
    <span style='color: #4466ff; font-size: 0.9rem;'>{ticker}</span>
    </div>
    """, unsafe_allow_html=True)

# ── Load ──────────────────────────────────────────────────────────────────────
with st.spinner(f"Fetching {ticker}..."):
    df, info = fetch(ticker, period)

if df is None or df.empty:
    st.error(f"❌ Could not fetch data for `{ticker}`. Check the ticker symbol.")
    st.markdown("**Examples:** `RELIANCE.NS` · `TCS.NS` · `AAPL` · `TSLA` · `NIFTY50.NS`")
    st.stop()

company_name = info.get("longName", ticker) if info else ticker
curr   = df["Close"].iloc[-1]
prev   = df["Close"].iloc[-2]
d_chg  = curr - prev
d_pct  = d_chg / prev * 100
tot    = df["CumRet"].iloc[-1]
rsi    = df["RSI"].iloc[-1]
vol    = df["Vol20"].mean()
hi52   = df["Close"].rolling(252).max().iloc[-1]
lo52   = df["Close"].rolling(252).min().iloc[-1]

# ════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="main-header">
    <div class="main-title">
        {company_name.split()[0]} <span>{company_name.split()[1] if len(company_name.split())>1 else ''}</span>
        <span class="ticker-badge">{ticker}</span>
    </div>
    <div class="main-sub">Real-time market analysis · {period} · {datetime.datetime.now().strftime('%d %b %Y %H:%M')}</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
up_dn  = "up" if d_pct >= 0 else "down"
tot_ud = "up" if tot >= 0 else "down"
rsi_cl = "warn" if rsi > 70 else "up" if rsi < 30 else "neu"
arrow  = "▲" if d_pct >= 0 else "▼"

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi neu">
        <div class="kpi-label">Last Price</div>
        <div class="kpi-val">{curr:.2f}</div>
        <div class="kpi-sub">52W H: {hi52:.2f} · L: {lo52:.2f}</div>
    </div>
    <div class="kpi {up_dn}">
        <div class="kpi-label">Day Change</div>
        <div class="kpi-val">{arrow} {abs(d_pct):.2f}%</div>
        <div class="kpi-sub">{d_chg:+.2f} pts</div>
    </div>
    <div class="kpi {tot_ud}">
        <div class="kpi-label">Period Return</div>
        <div class="kpi-val">{"▲" if tot>=0 else "▼"} {abs(tot):.1f}%</div>
        <div class="kpi-sub">{period} cumulative</div>
    </div>
    <div class="kpi {rsi_cl}">
        <div class="kpi-label">RSI (14)</div>
        <div class="kpi-val">{rsi:.1f}</div>
        <div class="kpi-sub">{"Overbought" if rsi>70 else "Oversold" if rsi<30 else "Neutral zone"}</div>
    </div>
    <div class="kpi warn">
        <div class="kpi-label">Volatility</div>
        <div class="kpi-val">{vol:.2f}%</div>
        <div class="kpi-sub">20D rolling std</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════
t1, t2, t3, t4 = st.tabs([
    "📊  Price & Volume",
    "📉  Indicators",
    "🔄  Compare",
    "💼  Portfolio",
])

# ── TAB 1: Price & Volume ─────────────────────────────────────────────────────
with t1:
    c1, c2 = st.columns([3,1])
    with c1:
        show_ma = st.checkbox("Moving Averages", True)
        show_bb = st.checkbox("Bollinger Bands", True)
    with c2:
        chart_type = st.radio("Chart", ["Candlestick","Line"], horizontal=True)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.75, 0.25], vertical_spacing=0.02,
    )

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df["Date"],
            open=df["Open"], high=df["High"],
            low=df["Low"],   close=df["Close"],
            increasing=dict(line_color=GREEN, fillcolor=GREEN),
            decreasing=dict(line_color=RED,   fillcolor=RED),
            name="Price", line_width=1,
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["Close"],
            line=dict(color=ACCENT, width=2),
            fill="tozeroy", fillcolor="rgba(68,102,255,0.05)",
            name="Close",
        ), row=1, col=1)

    if show_ma:
        for col, color, w in [("MA20","#ffaa00",1.2),("MA50","#aa44ff",1.2),("MA200","#ff44aa",1)]:
            if df[col].notna().any():
                fig.add_trace(go.Scatter(
                    x=df["Date"], y=df[col],
                    line=dict(color=color, width=w),
                    name=col, opacity=0.85,
                ), row=1, col=1)

    if show_bb:
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["BB_Up"],
            line=dict(color="#334466", width=1, dash="dot"),
            name="BB Upper", showlegend=True,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["BB_Lo"],
            line=dict(color="#334466", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(68,102,255,0.04)",
            name="BB Lower",
        ), row=1, col=1)

    # Volume bars
    vol_colors = [GREEN if c >= o else RED
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df["Date"], y=df["Volume"],
        marker_color=vol_colors, name="Volume",
        opacity=0.6, showlegend=False,
    ), row=2, col=1)

    themed(fig, height=550,
           xaxis_rangeslider_visible=False,
           title=f"{company_name} — {period}")
    fig.update_yaxes(title_text="Price", row=1, col=1, title_font_color=TEXT)
    fig.update_yaxes(title_text="Vol",   row=2, col=1, title_font_color=TEXT)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── TAB 2: Indicators ─────────────────────────────────────────────────────────
with t2:
    # RSI
    st.markdown('<div class="sec-label">RSI — Relative Strength Index (14)</div>', unsafe_allow_html=True)
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=df["Date"], y=df["RSI"],
        line=dict(color=ACCENT, width=1.8),
        fill="tozeroy", fillcolor="rgba(68,102,255,0.05)",
        name="RSI",
    ))
    fig_rsi.add_hline(y=70, line_color=RED,   line_dash="dash", line_width=1, annotation_text="70 Overbought", annotation_font_color=RED)
    fig_rsi.add_hline(y=30, line_color=GREEN, line_dash="dash", line_width=1, annotation_text="30 Oversold",   annotation_font_color=GREEN)
    fig_rsi.add_hrect(y0=70, y1=100, fillcolor=RED,   opacity=0.04)
    fig_rsi.add_hrect(y0=0,  y1=30,  fillcolor=GREEN, opacity=0.04)
    themed(fig_rsi, height=220)
    fig_rsi.update_yaxes(range=[0,100])
    st.plotly_chart(fig_rsi, use_container_width=True, config={"displayModeBar": False})

    # MACD
    st.markdown('<div class="sec-label">MACD — Moving Average Convergence Divergence</div>', unsafe_allow_html=True)
    fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True,
                             row_heights=[0.6, 0.4], vertical_spacing=0.04)
    fig_macd.add_trace(go.Scatter(x=df["Date"], y=df["MACD"],
        line=dict(color=ACCENT, width=1.5), name="MACD"), row=1, col=1)
    fig_macd.add_trace(go.Scatter(x=df["Date"], y=df["MACDs"],
        line=dict(color=AMBER, width=1.5), name="Signal"), row=1, col=1)
    hist_colors = [GREEN if v >= 0 else RED for v in df["MACDh"]]
    fig_macd.add_trace(go.Bar(x=df["Date"], y=df["MACDh"],
        marker_color=hist_colors, name="Histogram", opacity=0.7), row=2, col=1)
    themed(fig_macd, height=320)
    st.plotly_chart(fig_macd, use_container_width=True, config={"displayModeBar": False})

    # Volatility
    st.markdown('<div class="sec-label">Rolling Volatility (20D)</div>', unsafe_allow_html=True)
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Scatter(
        x=df["Date"], y=df["Vol20"],
        line=dict(color=AMBER, width=1.5),
        fill="tozeroy", fillcolor="rgba(255,170,0,0.05)",
        name="Volatility %",
    ))
    themed(fig_vol, height=180)
    st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": False})

    # Signals
    st.markdown('<div class="sec-label">Trading Signals</div>', unsafe_allow_html=True)
    macd_val = df["MACD"].iloc[-1]
    mac_sig  = df["MACDs"].iloc[-1]
    ma20v    = df["MA20"].iloc[-1]
    ma50v    = df["MA50"].iloc[-1]
    bbu      = df["BB_Up"].iloc[-1]
    bbl      = df["BB_Lo"].iloc[-1]
    close_v  = df["Close"].iloc[-1]

    sigs = [
        ("RSI", "bull" if rsi < 30 else "bear" if rsi > 70 else "neut",
         f"RSI {rsi:.1f} — {'Oversold → potential bounce' if rsi<30 else 'Overbought → potential pullback' if rsi>70 else 'Neutral — no strong signal'}"),
        ("MACD", "bull" if macd_val > mac_sig else "bear",
         f"MACD {macd_val:.3f} vs Signal {mac_sig:.3f} — {'Bullish crossover' if macd_val>mac_sig else 'Bearish crossover'}"),
        ("MA Cross", "bull" if ma20v > ma50v else "bear",
         f"MA20 ({ma20v:.1f}) {'above' if ma20v>ma50v else 'below'} MA50 ({ma50v:.1f}) — {'Golden Cross ↑' if ma20v>ma50v else 'Death Cross ↓'}"),
        ("Bollinger", "bull" if close_v < bbl else "bear" if close_v > bbu else "neut",
         f"Price {close_v:.1f} {'below lower band → oversold' if close_v<bbl else 'above upper band → overbought' if close_v>bbu else 'within bands → normal range'}"),
    ]

    c1, c2 = st.columns(2)
    for i, (name, cls, desc) in enumerate(sigs):
        col = c1 if i % 2 == 0 else c2
        with col:
            icon = "▲" if cls=="bull" else "▼" if cls=="bear" else "●"
            st.markdown(f'<div class="sig {cls}"><strong>{icon} {name}</strong><br>{desc}</div>',
                        unsafe_allow_html=True)

# ── TAB 3: Compare ────────────────────────────────────────────────────────────
with t3:
    st.markdown('<div class="sec-label">Compare multiple stocks</div>', unsafe_allow_html=True)

    compare_input = st.text_input(
        "Enter tickers separated by comma",
        value=f"{ticker}, TCS.NS, INFY.NS" if ".NS" in ticker else f"{ticker}, MSFT, GOOGL",
        placeholder="RELIANCE.NS, TCS.NS, AAPL"
    )

    tickers_list = [t.strip().upper() for t in compare_input.split(",") if t.strip()]

    if tickers_list:
        fig_cmp = go.Figure()
        perf_rows = []

        with st.spinner("Fetching comparison data..."):
            for i, t in enumerate(tickers_list[:6]):
                d, inf = fetch(t, period)
                if d is not None and not d.empty:
                    name = inf.get("shortName", t) if inf else t
                    fig_cmp.add_trace(go.Scatter(
                        x=d["Date"], y=d["CumRet"],
                        line=dict(color=PALETTE[i % len(PALETTE)], width=2),
                        name=f"{name} ({d['CumRet'].iloc[-1]:+.1f}%)",
                    ))
                    perf_rows.append({
                        "Ticker":    t,
                        "Company":   name,
                        "Price":     f"{d['Close'].iloc[-1]:.2f}",
                        "Return":    f"{d['CumRet'].iloc[-1]:+.1f}%",
                        "Volatility":f"{d['Vol20'].mean():.2f}%",
                        "RSI":       f"{d['RSI'].iloc[-1]:.1f}",
                    })

        fig_cmp.add_hline(y=0, line_color="#1e1e3a", line_width=1)
        themed(fig_cmp, height=400, title=f"Cumulative Returns — {period}")
        st.plotly_chart(fig_cmp, use_container_width=True, config={"displayModeBar": False})

        if perf_rows:
            st.dataframe(pd.DataFrame(perf_rows), use_container_width=True, hide_index=True)

# ── TAB 4: Portfolio ──────────────────────────────────────────────────────────
with t4:
    st.markdown('<div class="sec-label">Portfolio P&L Calculator</div>', unsafe_allow_html=True)
    st.caption("Enter ticker and quantity. Data fetched live from Yahoo Finance.")

    port_input = st.text_area(
        "Holdings (one per line: TICKER, QTY)",
        value="RELIANCE.NS, 10\nTCS.NS, 5\nAAPL, 8\nMSFT, 6",
        height=160,
    )

    if st.button("Calculate Portfolio", type="primary"):
        lines = [l.strip() for l in port_input.strip().split("\n") if l.strip()]
        rows  = []
        total_inv = total_curr = 0

        with st.spinner("Calculating..."):
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) != 2: continue
                tk, qty_str = parts
                try:
                    qty = float(qty_str)
                    d, inf = fetch(tk.upper(), "2y")
                    if d is None: continue
                    buy  = d["Close"].iloc[0]
                    curr = d["Close"].iloc[-1]
                    inv  = buy  * qty
                    now  = curr * qty
                    pnl  = now - inv
                    pct  = pnl / inv * 100
                    total_inv  += inv
                    total_curr += now
                    name = inf.get("shortName", tk) if inf else tk
                    rows.append({
                        "Ticker": tk.upper(), "Company": name, "Qty": int(qty),
                        "Buy Price": round(buy,2), "Current": round(curr,2),
                        "Invested": round(inv,2), "Value": round(now,2),
                        "P&L": round(pnl,2), "P&L %": round(pct,2),
                    })
                except:
                    continue

        if rows:
            total_pnl = total_curr - total_inv
            total_pct = total_pnl / total_inv * 100 if total_inv else 0
            pnl_col   = "up" if total_pnl >= 0 else "down"
            arrow     = "▲" if total_pnl >= 0 else "▼"

            st.markdown(f"""
            <div class="kpi-row">
                <div class="kpi neu">
                    <div class="kpi-label">Total Invested</div>
                    <div class="kpi-val">{total_inv:,.0f}</div>
                    <div class="kpi-sub">Initial capital</div>
                </div>
                <div class="kpi neu">
                    <div class="kpi-label">Current Value</div>
                    <div class="kpi-val">{total_curr:,.0f}</div>
                    <div class="kpi-sub">Market value today</div>
                </div>
                <div class="kpi {pnl_col}">
                    <div class="kpi-label">Total P&L</div>
                    <div class="kpi-val">{arrow} {abs(total_pnl):,.0f}</div>
                    <div class="kpi-sub">Unrealised gain/loss</div>
                </div>
                <div class="kpi {pnl_col}">
                    <div class="kpi-label">Return</div>
                    <div class="kpi-val">{arrow} {abs(total_pct):.1f}%</div>
                    <div class="kpi-sub">Overall return</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            df_p = pd.DataFrame(rows)
            st.dataframe(df_p, use_container_width=True, hide_index=True)

            c1, c2 = st.columns(2)
            with c1:
                fig_pie = go.Figure(go.Pie(
                    labels=df_p["Ticker"], values=df_p["Value"],
                    hole=0.65, marker_colors=PALETTE[:len(df_p)],
                    hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
                ))
                themed(fig_pie, height=300, title="Allocation")
                fig_pie.update_layout(showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

            with c2:
                bar_colors = [GREEN if v >= 0 else RED for v in df_p["P&L %"]]
                fig_bar = go.Figure(go.Bar(
                    x=df_p["Ticker"], y=df_p["P&L %"],
                    marker_color=bar_colors,
                    text=[f"{v:+.1f}%" for v in df_p["P&L %"]],
                    textposition="outside",
                ))
                fig_bar.add_hline(y=0, line_color="#1e1e3a", line_width=1)
                themed(fig_bar, height=300, title="P&L % by Stock")
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

# Footer
st.markdown("""
<div style='margin-top:32px; border-top:1px solid #1e1e3a; padding-top:12px;
font-family: IBM Plex Mono; font-size:0.6rem; color:#222244; letter-spacing:0.1em;'>
MARKETLENS · DATA VIA YAHOO FINANCE · FOR EDUCATIONAL USE ONLY · NOT FINANCIAL ADVICE
</div>
""", unsafe_allow_html=True)