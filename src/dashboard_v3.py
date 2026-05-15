"""
Stock Market Analytics Dashboard — v3
=======================================
New in v3:
  - Light / Dark theme toggle (sidebar button)
  - Fundamental Analysis tab — P/E, EPS, Market Cap, Dividends, Analyst Targets
  - Cleaner readable UI in both modes
  - Any stock search (NSE/BSE/US)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import warnings, datetime
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="MarketLens",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme state ───────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "light"

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 60

# ── Sidebar (theme toggle first) ──────────────────────────────────────────────
with st.sidebar:
    col_a, col_b = st.columns([3,1])
    with col_a:
        st.markdown("### 📡 MarketLens")
    with col_b:
        label = "🌙" if st.session_state.theme == "light" else "☀️"
        if st.button(label, help="Toggle dark / light"):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()

    # ── Auto Refresh Controls ─────────────────────────────────────────────────
    st.markdown("---")
    rc1, rc2 = st.columns([2,1])
    with rc1:
        auto_refresh = st.toggle("🔴 Live Refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
    with rc2:
        if auto_refresh:
            st.markdown(f"""
            <div style='background:{"#1a2a1a" if st.session_state.theme=="dark" else "#e8f8e8"};
            border:1px solid {"#00cc66" if st.session_state.theme=="dark" else "#00aa44"};
            border-radius:4px; padding:4px 8px; text-align:center;
            font-family:IBM Plex Mono; font-size:.6rem; color:{"#00cc66" if st.session_state.theme=="dark" else "#008844"};
            letter-spacing:.1em;'>
            ● LIVE
            </div>""", unsafe_allow_html=True)

    if auto_refresh:
        refresh_interval = st.select_slider(
            "Refresh every",
            options=[30, 60, 120, 300],
            value=st.session_state.refresh_interval,
            format_func=lambda x: f"{x}s" if x < 60 else f"{x//60}m"
        )
        st.session_state.refresh_interval = refresh_interval
        st.caption(f"Next refresh in {refresh_interval}s")

DARK = st.session_state.theme == "dark"

# ── Palette ───────────────────────────────────────────────────────────────────
if DARK:
    BG      = "#0b0b14"
    SURFACE = "#12121f"
    SURF2   = "#17172a"
    BORDER  = "#222238"
    TEXT    = "#c0c0e0"
    MUTED   = "#5a5a88"
    HEAD    = "#e4e4ff"
    ACCENT  = "#5b7fff"
    GREEN   = "#00cc66"
    RED     = "#ff3355"
    AMBER   = "#ffaa00"
    GRID    = "#191928"
    CBTN    = "#1c1c30"
else:
    BG      = "#f6f7fc"
    SURFACE = "#ffffff"
    SURF2   = "#eef0fa"
    BORDER  = "#dde0f2"
    TEXT    = "#2a2a55"
    MUTED   = "#8888bb"
    HEAD    = "#111133"
    ACCENT  = "#3355ee"
    GREEN   = "#008844"
    RED     = "#cc1133"
    AMBER   = "#bb7700"
    GRID    = "#eaecf8"
    CBTN    = "#e8eaf8"

PAL = [ACCENT,"#9944ff","#00aacc",GREEN,RED,AMBER,"#ee44aa","#33ccaa"]

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=Syne:wght@400;600;700;800&display=swap');

html,body,[class*="css"] {{ font-family:'Syne',sans-serif; background:{BG}!important; color:{TEXT}!important; }}
.stApp {{ background:{BG}!important; }}
section[data-testid="stSidebar"] {{ background:{SURFACE}!important; border-right:1px solid {BORDER}!important; }}
#MainMenu,footer {{ visibility:hidden; }}

/* KPI row */
.krow {{ display:flex; gap:10px; margin-bottom:18px; flex-wrap:wrap; }}
.kpi {{
    flex:1; min-width:130px;
    background:{SURFACE}; border:1px solid {BORDER}; border-top:3px solid;
    padding:14px 16px; border-radius:6px;
    font-family:'IBM Plex Mono',monospace;
    box-shadow:{"0 2px 8px rgba(0,0,0,0.3)" if DARK else "0 1px 6px rgba(80,80,160,0.08)"};
}}
.kpi.up   {{ border-top-color:{GREEN};  }}
.kpi.dn   {{ border-top-color:{RED};    }}
.kpi.nu   {{ border-top-color:{ACCENT}; }}
.kpi.wa   {{ border-top-color:{AMBER};  }}
.klabel   {{ font-size:.57rem; letter-spacing:.18em; color:{MUTED}; text-transform:uppercase; margin-bottom:5px; }}
.kval     {{ font-size:1.3rem; font-weight:600; letter-spacing:-.02em; line-height:1; color:{HEAD}; }}
.kpi.up .kval {{ color:{GREEN}; }}
.kpi.dn .kval {{ color:{RED};   }}
.kpi.nu .kval {{ color:{ACCENT};}}
.kpi.wa .kval {{ color:{AMBER}; }}
.ksub     {{ font-size:.6rem; color:{MUTED}; margin-top:4px; }}

/* Section label */
.slabel {{
    font-family:'IBM Plex Mono',monospace; font-size:.56rem;
    letter-spacing:.2em; color:{MUTED}; text-transform:uppercase;
    border-left:2px solid {ACCENT}; padding-left:9px; margin:20px 0 11px;
}}

/* Signal cards */
.sig {{
    background:{SURF2}; border:1px solid {BORDER}; border-left:3px solid;
    padding:11px 14px; margin-bottom:7px; border-radius:0 5px 5px 0;
    font-family:'IBM Plex Mono',monospace; font-size:.76rem; color:{TEXT}; line-height:1.6;
}}
.sig.bl {{ border-left-color:{GREEN}; }}
.sig.br {{ border-left-color:{RED};   }}
.sig.bn {{ border-left-color:{ACCENT};}}
.sig strong {{ color:{HEAD}; }}

/* Fundamental grid */
.fgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:10px; margin-bottom:18px; }}
.fc {{
    background:{SURFACE}; border:1px solid {BORDER}; border-radius:6px;
    padding:14px 16px;
    box-shadow:{"0 2px 8px rgba(0,0,0,0.25)" if DARK else "0 1px 5px rgba(80,80,160,0.07)"};
}}
.fl {{ font-family:'IBM Plex Mono',monospace; font-size:.55rem; letter-spacing:.15em; color:{MUTED}; text-transform:uppercase; margin-bottom:5px; }}
.fv {{ font-family:'IBM Plex Mono',monospace; font-size:1rem; font-weight:600; color:{HEAD}; }}
.fs {{ font-size:.65rem; color:{MUTED}; margin-top:2px; }}

/* About box */
.abox {{
    background:{SURF2}; border:1px solid {BORDER}; border-radius:6px;
    padding:18px 20px; font-size:.85rem; line-height:1.75; color:{TEXT};
    margin-bottom:16px;
}}
.abox b {{ color:{HEAD}; }}

/* Header */
.mhdr {{ border-bottom:1px solid {BORDER}; padding-bottom:12px; margin-bottom:16px; }}
.mtitle {{ font-family:'Syne',sans-serif; font-size:1.65rem; font-weight:800; color:{HEAD}; letter-spacing:-.02em; line-height:1; }}
.mtitle span {{ color:{ACCENT}; }}
.tbadge {{
    display:inline-block; background:{"rgba(91,127,255,.12)" if DARK else "rgba(51,85,238,.07)"};
    border:1px solid {ACCENT}; color:{ACCENT};
    font-family:'IBM Plex Mono',monospace; font-size:.66rem;
    padding:3px 9px; letter-spacing:.08em; margin-left:8px; vertical-align:middle; border-radius:3px;
}}
.msub {{ font-family:'IBM Plex Mono',monospace; font-size:.58rem; color:{MUTED}; letter-spacing:.12em; margin-top:3px; text-transform:uppercase; }}

/* Inputs */
.stTextInput input,.stTextArea textarea {{
    background:{SURFACE}!important; border:1px solid {BORDER}!important;
    color:{HEAD}!important; font-family:'IBM Plex Mono',monospace!important; border-radius:5px!important;
}}
.stSelectbox>div>div {{ background:{SURFACE}!important; border:1px solid {BORDER}!important; color:{HEAD}!important; border-radius:5px!important; }}
label,.stCheckbox span,.stRadio span {{ color:{TEXT}!important; }}
h1,h2,h3 {{ color:{HEAD}!important; }}
hr {{ border-color:{BORDER}!important; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ background:transparent!important; border-bottom:1px solid {BORDER}!important; gap:0!important; }}
.stTabs [data-baseweb="tab"] {{
    background:transparent!important; color:{MUTED}!important;
    font-family:'IBM Plex Mono',monospace!important; font-size:.68rem!important;
    letter-spacing:.08em!important; text-transform:uppercase!important;
    padding:9px 18px!important; border-bottom:2px solid transparent!important;
}}
.stTabs [aria-selected="true"] {{ color:{ACCENT}!important; border-bottom:2px solid {ACCENT}!important; background:transparent!important; }}
</style>
""", unsafe_allow_html=True)

# ── Plotly base ───────────────────────────────────────────────────────────────
BLAYOUT = dict(
    plot_bgcolor  = SURFACE,
    paper_bgcolor = BG,
    font          = dict(family="IBM Plex Mono", color=TEXT, size=11),
    title_font    = dict(color=HEAD, size=13, family="Syne"),
    margin        = dict(l=8, r=8, t=36, b=8),
    legend        = dict(bgcolor=SURF2, bordercolor=BORDER, borderwidth=1, font_size=10, font_color=TEXT),
    xaxis = dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED, showgrid=True, zeroline=False),
    yaxis = dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED, showgrid=True, zeroline=False),
)

def th(fig, h=400, **kw):
    fig.update_layout(**BLAYOUT, height=h, **kw)
    fig.update_xaxes(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED)
    fig.update_yaxes(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED)
    return fig

# ── Helpers ───────────────────────────────────────────────────────────────────
def fl(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "N/A"
    try:
        v = float(v)
        if v >= 1e12: return f"{v/1e12:.2f} T"
        if v >= 1e9:  return f"{v/1e9:.2f} B"
        if v >= 1e6:  return f"{v/1e6:.2f} M"
        return f"{v:,.0f}"
    except: return "N/A"

def fp(v):
    if v is None: return "N/A"
    try: return f"{float(v)*100:.2f}%"
    except: return "N/A"

def fv(v, d=2):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "N/A"
    try: return f"{float(v):,.{d}f}"
    except: return "N/A"

def indicators(df):
    df = df.copy()
    df["MA20"]  = df["Close"].rolling(20).mean()
    df["MA50"]  = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["V20"]   = df["Close"].pct_change().rolling(20).std() * 100
    df["BBm"]   = df["Close"].rolling(20).mean()
    df["BBs"]   = df["Close"].rolling(20).std()
    df["BBu"]   = df["BBm"] + 2*df["BBs"]
    df["BBl"]   = df["BBm"] - 2*df["BBs"]
    d = df["Close"].diff()
    g = d.clip(lower=0).rolling(14).mean()
    l = (-d.clip(upper=0)).rolling(14).mean()
    df["RSI"]   = 100 - 100/(1 + g/l.replace(0, np.nan))
    e12 = df["Close"].ewm(span=12, adjust=False).mean()
    e26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]  = e12 - e26
    df["MACDs"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACDh"] = df["MACD"] - df["MACDs"]
    df["Ret"]   = df["Close"].pct_change() * 100
    df["CRet"]  = (df["Close"]/df["Close"].iloc[0] - 1) * 100
    return df

@st.cache_data(ttl=300)
def fetch(ticker, period="1y"):
    try:
        t  = yf.Ticker(ticker)
        df = t.history(period=period)
        if df.empty: return None, None
        df = df.reset_index()[["Date","Open","High","Low","Close","Volume"]]
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        return indicators(df), t.info
    except: return None, None

QUICK = {
    "🇮🇳 India (NSE)": {
        "RELIANCE.NS":"Reliance","TCS.NS":"TCS","HDFCBANK.NS":"HDFC Bank",
        "INFY.NS":"Infosys","WIPRO.NS":"Wipro","TATAMOTORS.NS":"Tata Motors",
        "ADANIENT.NS":"Adani Ent.","BAJFINANCE.NS":"Bajaj Finance",
        "SUNPHARMA.NS":"Sun Pharma","MARUTI.NS":"Maruti Suzuki",
    },
    "🇺🇸 US": {
        "AAPL":"Apple","MSFT":"Microsoft","GOOGL":"Google","AMZN":"Amazon",
        "NVDA":"Nvidia","TSLA":"Tesla","META":"Meta","NFLX":"Netflix",
    },
}

# ── Sidebar (rest) ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown(f"<p style='font-family:IBM Plex Mono;font-size:.58rem;color:{MUTED};letter-spacing:.15em'>SEARCH ANY STOCK</p>", unsafe_allow_html=True)
    custom = st.text_input("", placeholder="INFY.NS · NVDA · TSLA", label_visibility="collapsed").upper().strip()

    st.markdown(f"<p style='font-family:IBM Plex Mono;font-size:.58rem;color:{MUTED};letter-spacing:.15em'>OR PICK FROM LIST</p>", unsafe_allow_html=True)
    mkt    = st.selectbox("Market", list(QUICK.keys()), label_visibility="collapsed")
    picked = st.selectbox("Stock",  list(QUICK[mkt].values()), label_visibility="collapsed")
    ptick  = {v:k for k,v in QUICK[mkt].items()}[picked]
    ticker = custom if custom else ptick
    period = st.select_slider("Period", ["1mo","3mo","6mo","1y","2y","5y"], value="1y")

    st.markdown("---")
    st.markdown(f"<p style='font-family:IBM Plex Mono;font-size:.58rem;color:{MUTED}'>ACTIVE TICKER</p><p style='font-family:IBM Plex Mono;font-size:.95rem;font-weight:600;color:{ACCENT}'>{ticker}</p>", unsafe_allow_html=True)

# ── Load ──────────────────────────────────────────────────────────────────────
with st.spinner(f"Loading {ticker}..."):
    df, info = fetch(ticker, period)

if df is None or df.empty:
    st.error(f"❌ Could not fetch `{ticker}`. Try: `RELIANCE.NS` · `AAPL` · `TSLA`")
    st.stop()

name  = info.get("longName", ticker) if info else ticker
cur   = df["Close"].iloc[-1]
prv   = df["Close"].iloc[-2]
dchg  = cur - prv
dpct  = dchg / prv * 100
tot   = df["CRet"].iloc[-1]
rsi   = df["RSI"].dropna().iloc[-1] if df["RSI"].notna().any() else 50
vol   = df["V20"].mean()
hi52  = df["Close"].rolling(min(252,len(df))).max().iloc[-1]
lo52  = df["Close"].rolling(min(252,len(df))).min().iloc[-1]

# ── Header ────────────────────────────────────────────────────────────────────
words = name.split(); w1 = words[0]; wrest = " ".join(words[1:])
st.markdown(f"""
<div class="mhdr">
  <div class="mtitle">{w1} <span>{wrest}</span><span class="tbadge">{ticker}</span></div>
  <div class="msub">Real-time analysis · {period} · {datetime.datetime.now().strftime('%d %b %Y %H:%M')}</div>
</div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
uc = "up" if dpct >= 0 else "dn"
tc = "up" if tot  >= 0 else "dn"
rc = "wa" if rsi > 70 else "up" if rsi < 30 else "nu"
ar = "▲" if dpct >= 0 else "▼"
ar2= "▲" if tot  >= 0 else "▼"

st.markdown(f"""<div class="krow">
  <div class="kpi nu"><div class="klabel">Last Price</div><div class="kval">{cur:.2f}</div>
    <div class="ksub">52W H:{hi52:.1f} · L:{lo52:.1f}</div></div>
  <div class="kpi {uc}"><div class="klabel">Day Change</div><div class="kval">{ar} {abs(dpct):.2f}%</div>
    <div class="ksub">{dchg:+.2f} pts</div></div>
  <div class="kpi {tc}"><div class="klabel">Period Return</div><div class="kval">{ar2} {abs(tot):.1f}%</div>
    <div class="ksub">{period} cumulative</div></div>
  <div class="kpi {rc}"><div class="klabel">RSI (14)</div><div class="kval">{rsi:.1f}</div>
    <div class="ksub">{"⚠ Overbought" if rsi>70 else "⚡ Oversold" if rsi<30 else "Neutral"}</div></div>
  <div class="kpi wa"><div class="klabel">Volatility</div><div class="kval">{vol:.2f}%</div>
    <div class="ksub">20D rolling std</div></div>
</div>""", unsafe_allow_html=True)

# ── Live Ticker Tape ──────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_ticker_tape():
    """Fetch quick prices for ticker tape"""
    tape_stocks = {
        "RELIANCE.NS":"RELIANCE","TCS.NS":"TCS","HDFCBANK.NS":"HDFC",
        "INFY.NS":"INFY","AAPL":"AAPL","MSFT":"MSFT","NVDA":"NVDA","TSLA":"TSLA"
    }
    items = []
    for tk, short in tape_stocks.items():
        try:
            d = yf.Ticker(tk).history(period="2d")
            if len(d) >= 2:
                c = d["Close"].iloc[-1]
                p = d["Close"].iloc[-2]
                chg = (c-p)/p*100
                items.append((short, c, chg))
        except: pass
    return items

tape_items = fetch_ticker_tape()
if tape_items:
    tape_html = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join([
        f"<span style='color:{GREEN if chg>=0 else RED}'>"
        f"<b>{nm}</b> {price:.1f} "
        f"{'▲' if chg>=0 else '▼'}{abs(chg):.2f}%</span>"
        for nm, price, chg in tape_items
    ])
    st.markdown(f"""
    <div style='background:{SURF2};border:1px solid {BORDER};border-radius:4px;
    padding:8px 16px;margin-bottom:16px;overflow:hidden;white-space:nowrap;'>
    <span style='font-family:IBM Plex Mono;font-size:.72rem;color:{MUTED};
    letter-spacing:.05em;'>
    📡 &nbsp; {tape_html}
    </span>
    </div>
    """, unsafe_allow_html=True)

# ── Auto Refresh Logic ────────────────────────────────────────────────────────
if st.session_state.auto_refresh:
    import time
    refresh_interval = st.session_state.refresh_interval
    # Show countdown
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
        <div style='font-family:IBM Plex Mono;font-size:.6rem;color:{MUTED};
        text-align:right;margin-bottom:4px;'>
        🔄 Auto-refreshing every {refresh_interval}s · Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}
        </div>""", unsafe_allow_html=True)
    time.sleep(refresh_interval)
    st.cache_data.clear()
    st.rerun()

# ── Tabs ──────────────────────────────────────────────────────────────────────
T1,T2,T3,T4,T5,T6,T7,T8,T9,T10,T11,T12,T13,T14,T15 = st.tabs(["📊  Price","📉  Indicators","🏢  Fundamentals","🔄  Compare","💼  Portfolio","📰  News","⚡  Advanced","🎯  Patterns & Tools","🤖  ML Forecast","📈  Options Chain","🌍  Sector Heatmap","📅  Earnings","💹  Crypto & Forex","🔍  Screener","🔔  Alerts"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — PRICE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T1:
    c1,c2,c3 = st.columns(3)
    with c1: sma = st.checkbox("Moving Averages", True)
    with c2: sbb = st.checkbox("Bollinger Bands", True)
    with c3: ct  = st.radio("Type", ["Candlestick","Line"], horizontal=True)

    fig = make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[.75,.25],vertical_spacing=.02)
    if ct=="Candlestick":
        fig.add_trace(go.Candlestick(x=df["Date"],open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],
            increasing=dict(line_color=GREEN,fillcolor=GREEN),decreasing=dict(line_color=RED,fillcolor=RED),
            name="Price",line_width=1),row=1,col=1)
    else:
        fig.add_trace(go.Scatter(x=df["Date"],y=df["Close"],line=dict(color=ACCENT,width=2),
            fill="tozeroy",fillcolor=f"{'rgba(91,127,255,.07)' if DARK else 'rgba(51,85,238,.05)'}",name="Close"),row=1,col=1)
    if sma:
        for col,clr,w in [("MA20",AMBER,1.3),("MA50","#9944ff",1.3),("MA200","#ee44aa",1)]:
            if df[col].notna().any():
                fig.add_trace(go.Scatter(x=df["Date"],y=df[col],line=dict(color=clr,width=w),name=col,opacity=.9),row=1,col=1)
    if sbb:
        fig.add_trace(go.Scatter(x=df["Date"],y=df["BBu"],line=dict(color=MUTED,width=1,dash="dot"),name="BB Up"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df["Date"],y=df["BBl"],line=dict(color=MUTED,width=1,dash="dot"),
            fill="tonexty",fillcolor=f"{'rgba(100,100,180,.05)' if DARK else 'rgba(51,85,238,.04)'}",name="BB Lo"),row=1,col=1)
    vc = [GREEN if c>=o else RED for c,o in zip(df["Close"],df["Open"])]
    fig.add_trace(go.Bar(x=df["Date"],y=df["Volume"],marker_color=vc,name="Vol",opacity=.55,showlegend=False),row=2,col=1)
    th(fig,h=520,xaxis_rangeslider_visible=False,title=f"{name} · {period}")
    fig.update_yaxes(title_text="Price",row=1,col=1,title_font_color=MUTED)
    fig.update_yaxes(title_text="Vol",  row=2,col=1,title_font_color=MUTED)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — INDICATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T2:
    st.markdown('<div class="slabel">RSI — Relative Strength Index (14)</div>',unsafe_allow_html=True)
    fr = go.Figure()
    fr.add_trace(go.Scatter(x=df["Date"],y=df["RSI"],line=dict(color=ACCENT,width=2),
        fill="tozeroy",fillcolor=f"{'rgba(91,127,255,.07)' if DARK else 'rgba(51,85,238,.05)'}",name="RSI"))
    fr.add_hline(y=70,line_color=RED,  line_dash="dash",line_width=1,annotation_text="70 Overbought",annotation_font_color=RED,  annotation_font_size=10)
    fr.add_hline(y=30,line_color=GREEN,line_dash="dash",line_width=1,annotation_text="30 Oversold",  annotation_font_color=GREEN,annotation_font_size=10)
    fr.add_hrect(y0=70,y1=100,fillcolor=RED,  opacity=.04)
    fr.add_hrect(y0=0, y1=30, fillcolor=GREEN,opacity=.04)
    th(fr,h=220); fr.update_yaxes(range=[0,100])
    st.plotly_chart(fr,use_container_width=True,config={"displayModeBar":False})

    st.markdown('<div class="slabel">MACD</div>',unsafe_allow_html=True)
    fm = make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[.55,.45],vertical_spacing=.04)
    fm.add_trace(go.Scatter(x=df["Date"],y=df["MACD"], line=dict(color=ACCENT,width=1.8),name="MACD"),  row=1,col=1)
    fm.add_trace(go.Scatter(x=df["Date"],y=df["MACDs"],line=dict(color=AMBER, width=1.8),name="Signal"),row=1,col=1)
    hc=[GREEN if v>=0 else RED for v in df["MACDh"]]
    fm.add_trace(go.Bar(x=df["Date"],y=df["MACDh"],marker_color=hc,name="Hist",opacity=.65),row=2,col=1)
    th(fm,h=290); st.plotly_chart(fm,use_container_width=True,config={"displayModeBar":False})

    st.markdown('<div class="slabel">20D Rolling Volatility</div>',unsafe_allow_html=True)
    fv2=go.Figure()
    fv2.add_trace(go.Scatter(x=df["Date"],y=df["V20"],line=dict(color=AMBER,width=1.8),
        fill="tozeroy",fillcolor=f"{'rgba(255,170,0,.06)' if DARK else 'rgba(187,119,0,.05)'}",name="Vol%"))
    th(fv2,h=170); st.plotly_chart(fv2,use_container_width=True,config={"displayModeBar":False})

    st.markdown('<div class="slabel">Trading Signals</div>',unsafe_allow_html=True)
    mv=df["MACD"].iloc[-1]; ms=df["MACDs"].iloc[-1]
    m20=df["MA20"].iloc[-1] if df["MA20"].notna().any() else cur
    m50=df["MA50"].iloc[-1] if df["MA50"].notna().any() else cur
    bu=df["BBu"].iloc[-1]; bl=df["BBl"].iloc[-1]
    sigs=[
        ("RSI","bl" if rsi<30 else "br" if rsi>70 else "bn",
         f"RSI {rsi:.1f} — {'Oversold → bounce likely' if rsi<30 else 'Overbought → pullback risk' if rsi>70 else 'Neutral zone'}"),
        ("MACD","bl" if mv>ms else "br",
         f"MACD {mv:.3f} vs Signal {ms:.3f} — {'Bullish ↑' if mv>ms else 'Bearish ↓'}"),
        ("MA Cross","bl" if m20>m50 else "br",
         f"MA20 ({m20:.1f}) {'above' if m20>m50 else 'below'} MA50 ({m50:.1f}) — {'Golden Cross ↑' if m20>m50 else 'Death Cross ↓'}"),
        ("Bollinger","bl" if cur<bl else "br" if cur>bu else "bn",
         f"Price {cur:.1f} — {'Below lower band → oversold' if cur<bl else 'Above upper band → overbought' if cur>bu else 'Within bands → normal'}"),
    ]
    c1,c2=st.columns(2)
    for i,(nm,cls,desc) in enumerate(sigs):
        icon="▲" if cls=="bl" else "▼" if cls=="br" else "●"
        with (c1 if i%2==0 else c2):
            st.markdown(f'<div class="sig {cls}"><strong>{icon} {nm}</strong><br>{desc}</div>',unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — FUNDAMENTALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T3:
    if not info:
        st.warning("Fundamental data not available for this ticker.")
    else:
        about    = info.get("longBusinessSummary","")
        sector   = info.get("sector","N/A")
        industry = info.get("industry","N/A")
        country  = info.get("country","N/A")
        emp      = info.get("fullTimeEmployees")
        website  = info.get("website","")

        st.markdown('<div class="slabel">Company Overview</div>',unsafe_allow_html=True)
        mc=st.columns(4)
        for col,lab,val in zip(mc,["Sector","Industry","Country","Employees"],
            [sector,industry,country,f"{emp:,}" if emp else "N/A"]):
            with col:
                st.markdown(f'<div class="fc"><div class="fl">{lab}</div><div class="fv" style="font-size:.85rem">{val}</div></div>',unsafe_allow_html=True)
        if about:
            link = f"<br><a href='{website}' style='color:{ACCENT};font-size:.75rem'>{website}</a>" if website else ""
            st.markdown(f'<div class="abox">{about[:650]}{"..." if len(about)>650 else ""}{link}</div>',unsafe_allow_html=True)

        # Valuation
        st.markdown('<div class="slabel">Valuation</div>',unsafe_allow_html=True)
        vm=[("Market Cap",fl(info.get("marketCap")),"Total company value"),
            ("P/E (TTM)",fv(info.get("trailingPE")),"Price / Earnings"),
            ("Forward P/E",fv(info.get("forwardPE")),"Next yr estimate"),
            ("P/B Ratio",fv(info.get("priceToBook")),"Price / Book"),
            ("P/S Ratio",fv(info.get("priceToSalesTrailing12Months")),"Price / Sales"),
            ("EV/EBITDA",fv(info.get("enterpriseToEbitda")),"Enterprise ratio"),
            ("Enterprise Value",fl(info.get("enterpriseValue")),"Mkt cap + debt - cash"),
            ("PEG Ratio",fv(info.get("pegRatio")),"P/E / Growth")]
        st.markdown('<div class="fgrid">'+''.join([f'<div class="fc"><div class="fl">{l}</div><div class="fv">{v}</div><div class="fs">{s}</div></div>' for l,v,s in vm])+'</div>',unsafe_allow_html=True)

        # Financials
        st.markdown('<div class="slabel">Financial Performance</div>',unsafe_allow_html=True)
        fm2=[("Revenue (TTM)",fl(info.get("totalRevenue")),"Annual revenue"),
             ("Gross Profit",fl(info.get("grossProfits")),"Revenue - COGS"),
             ("EBITDA",fl(info.get("ebitda")),"Earnings before int/tax"),
             ("Net Income",fl(info.get("netIncomeToCommon")),"Bottom line"),
             ("EPS (TTM)",fv(info.get("trailingEps")),"Earnings per share"),
             ("EPS Forward",fv(info.get("forwardEps")),"Next yr EPS est."),
             ("Revenue Growth",fp(info.get("revenueGrowth")),"YoY growth"),
             ("Earnings Growth",fp(info.get("earningsGrowth")),"YoY earnings")]
        st.markdown('<div class="fgrid">'+''.join([f'<div class="fc"><div class="fl">{l}</div><div class="fv">{v}</div><div class="fs">{s}</div></div>' for l,v,s in fm2])+'</div>',unsafe_allow_html=True)

        # Dividends & Balance
        st.markdown('<div class="slabel">Dividends & Balance Sheet</div>',unsafe_allow_html=True)
        db=[("Dividend Yield",fp(info.get("dividendYield")),"Annual div / price"),
            ("Dividend Rate",fv(info.get("dividendRate")),"Annual div per share"),
            ("Payout Ratio",fp(info.get("payoutRatio")),"% earnings as div"),
            ("Total Cash",fl(info.get("totalCash")),"Cash & equivalents"),
            ("Total Debt",fl(info.get("totalDebt")),"Short + long term"),
            ("Debt / Equity",fv(info.get("debtToEquity")),"Leverage ratio"),
            ("Return on Equity",fp(info.get("returnOnEquity")),"Net income / equity"),
            ("Return on Assets",fp(info.get("returnOnAssets")),"Net income / assets")]
        st.markdown('<div class="fgrid">'+''.join([f'<div class="fc"><div class="fl">{l}</div><div class="fv">{v}</div><div class="fs">{s}</div></div>' for l,v,s in db])+'</div>',unsafe_allow_html=True)

        # Analyst targets
        thi=info.get("targetHighPrice"); tlo=info.get("targetLowPrice")
        tme=info.get("targetMeanPrice"); rec=info.get("recommendationKey","").upper().replace("_"," ")
        if tme:
            st.markdown('<div class="slabel">Analyst Targets</div>',unsafe_allow_html=True)
            ups=((tme-cur)/cur*100) if cur else 0
            uc2="up" if ups>=0 else "dn"; ar3="▲" if ups>=0 else "▼"
            st.markdown(f"""<div class="krow">
              <div class="kpi nu"><div class="klabel">Current</div><div class="kval">{cur:.2f}</div></div>
              <div class="kpi nu"><div class="klabel">Target Low</div><div class="kval">{fv(tlo)}</div></div>
              <div class="kpi nu"><div class="klabel">Target Mean</div><div class="kval">{fv(tme)}</div></div>
              <div class="kpi nu"><div class="klabel">Target High</div><div class="kval">{fv(thi)}</div></div>
              <div class="kpi {uc2}"><div class="klabel">Upside</div><div class="kval">{ar3} {abs(ups):.1f}%</div>
                <div class="ksub">{rec}</div></div>
            </div>""",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — COMPARE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T4:
    ci = st.text_input("Tickers (comma separated)",
        value=f"{ticker}, TCS.NS, INFY.NS" if ".NS" in ticker else f"{ticker}, MSFT, GOOGL")
    tl = [t.strip().upper() for t in ci.split(",") if t.strip()]
    if tl:
        fc=go.Figure(); rows=[]
        with st.spinner("Fetching..."):
            for i,t in enumerate(tl[:6]):
                d,inf=fetch(t,period)
                if d is not None and not d.empty:
                    nm=inf.get("shortName",t) if inf else t
                    ret=d["CRet"].iloc[-1]
                    fc.add_trace(go.Scatter(x=d["Date"],y=d["CRet"],
                        line=dict(color=PAL[i%len(PAL)],width=2),
                        name=f"{nm} ({ret:+.1f}%)"))
                    rows.append({"Ticker":t,"Company":nm,
                        "Price":f"{d['Close'].iloc[-1]:.2f}",
                        "Return":f"{ret:+.1f}%",
                        "Volatility":f"{d['V20'].mean():.2f}%",
                        "RSI":f"{d['RSI'].dropna().iloc[-1]:.1f}"})
        fc.add_hline(y=0,line_color=BORDER,line_width=1)
        th(fc,h=400,title=f"Cumulative Returns — {period}")
        st.plotly_chart(fc,use_container_width=True,config={"displayModeBar":False})
        if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5 — PORTFOLIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T5:
    st.caption("Format: TICKER, QUANTITY — one per line")
    pi=st.text_area("Holdings","RELIANCE.NS, 10\nTCS.NS, 5\nAAPL, 8\nMSFT, 6",height=140)
    if st.button("Calculate Portfolio ▶",type="primary"):
        lines=[l.strip() for l in pi.strip().split("\n") if l.strip()]
        rows=[]; ti=tc2=0
        with st.spinner("Fetching live prices..."):
            for line in lines:
                parts=[p.strip() for p in line.split(",")]
                if len(parts)!=2: continue
                tk,qs=parts
                try:
                    qty=float(qs); d,inf=fetch(tk.upper(),"2y")
                    if d is None: continue
                    bp=d["Close"].iloc[0]; cp=d["Close"].iloc[-1]
                    inv=bp*qty; now=cp*qty; pnl=now-inv; pct=pnl/inv*100
                    ti+=inv; tc2+=now
                    nm=inf.get("shortName",tk) if inf else tk
                    rows.append({"Ticker":tk.upper(),"Company":nm,"Qty":int(qty),
                        "Buy":round(bp,2),"Current":round(cp,2),
                        "Invested":round(inv,2),"Value":round(now,2),
                        "P&L":round(pnl,2),"P&L%":round(pct,2)})
                except: continue
        if rows:
            tp=tc2-ti; tpct=tp/ti*100 if ti else 0
            pc="up" if tp>=0 else "dn"; ar4="▲" if tp>=0 else "▼"
            st.markdown(f"""<div class="krow">
              <div class="kpi nu"><div class="klabel">Invested</div><div class="kval">{ti:,.0f}</div></div>
              <div class="kpi nu"><div class="klabel">Current Value</div><div class="kval">{tc2:,.0f}</div></div>
              <div class="kpi {pc}"><div class="klabel">Total P&L</div><div class="kval">{ar4} {abs(tp):,.0f}</div></div>
              <div class="kpi {pc}"><div class="klabel">Return</div><div class="kval">{ar4} {abs(tpct):.1f}%</div></div>
            </div>""",unsafe_allow_html=True)
            dfp=pd.DataFrame(rows)
            st.dataframe(dfp,use_container_width=True,hide_index=True)
            c1,c2=st.columns(2)
            with c1:
                fp2=go.Figure(go.Pie(labels=dfp["Ticker"],values=dfp["Value"],hole=.62,
                    marker_colors=PAL[:len(dfp)],hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>"))
                th(fp2,h=300,title="Allocation"); fp2.update_layout(showlegend=True)
                st.plotly_chart(fp2,use_container_width=True,config={"displayModeBar":False})
            with c2:
                bc=[GREEN if v>=0 else RED for v in dfp["P&L%"]]
                fb=go.Figure(go.Bar(x=dfp["Ticker"],y=dfp["P&L%"],marker_color=bc,
                    text=[f"{v:+.1f}%" for v in dfp["P&L%"]],textposition="outside",textfont_color=TEXT))
                fb.add_hline(y=0,line_color=BORDER,line_width=1)
                th(fb,h=300,title="P&L % by Stock")
                st.plotly_chart(fb,use_container_width=True,config={"displayModeBar":False})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 7 — ADVANCED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T7:

    # ── Risk Metrics ─────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Risk & Performance Metrics</div>', unsafe_allow_html=True)

    returns     = df["Ret"].dropna() / 100
    daily_mean  = returns.mean()
    daily_std   = returns.std()
    trading_days= 252

    # Sharpe Ratio (assuming risk-free rate = 6% for India, 5% for US)
    rf = 0.06 / trading_days if ".NS" in ticker else 0.05 / trading_days
    sharpe = (daily_mean - rf) / daily_std * np.sqrt(trading_days) if daily_std > 0 else 0

    # Sortino Ratio (downside deviation only)
    downside = returns[returns < 0].std()
    sortino  = (daily_mean - rf) / downside * np.sqrt(trading_days) if downside > 0 else 0

    # Max Drawdown
    cum_returns  = (1 + returns).cumprod()
    rolling_max  = cum_returns.cummax()
    drawdown     = (cum_returns - rolling_max) / rolling_max
    max_drawdown = drawdown.min() * 100

    # Annualized Return & Volatility
    ann_return = ((1 + daily_mean) ** trading_days - 1) * 100
    ann_vol    = daily_std * np.sqrt(trading_days) * 100

    # Calmar Ratio
    calmar = ann_return / abs(max_drawdown) if max_drawdown != 0 else 0

    # Win Rate
    win_rate = (returns > 0).mean() * 100

    # VaR (95% confidence)
    var_95 = returns.quantile(0.05) * 100

    sc = "up" if sharpe > 1 else "wa" if sharpe > 0 else "dn"
    st.markdown(f"""<div class="krow">
      <div class="kpi {sc}"><div class="klabel">Sharpe Ratio</div><div class="kval">{sharpe:.2f}</div>
        <div class="ksub">{"Excellent" if sharpe>2 else "Good" if sharpe>1 else "Average" if sharpe>0 else "Poor"} · Risk-adj return</div></div>
      <div class="kpi {'up' if sortino>1 else 'wa' if sortino>0 else 'dn'}">
        <div class="klabel">Sortino Ratio</div><div class="kval">{sortino:.2f}</div>
        <div class="ksub">Downside risk adjusted</div></div>
      <div class="kpi dn"><div class="klabel">Max Drawdown</div><div class="kval">{max_drawdown:.1f}%</div>
        <div class="ksub">Worst peak-to-trough</div></div>
      <div class="kpi nu"><div class="klabel">Ann. Return</div><div class="kval">{ann_return:+.1f}%</div>
        <div class="ksub">Annualized</div></div>
      <div class="kpi wa"><div class="klabel">Ann. Volatility</div><div class="kval">{ann_vol:.1f}%</div>
        <div class="ksub">Annualized std dev</div></div>
      <div class="kpi nu"><div class="klabel">Win Rate</div><div class="kval">{win_rate:.1f}%</div>
        <div class="ksub">Days with +ve return</div></div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="krow">
          <div class="kpi wa"><div class="klabel">Calmar Ratio</div><div class="kval">{calmar:.2f}</div>
            <div class="ksub">Return / Max Drawdown</div></div>
          <div class="kpi dn"><div class="klabel">VaR (95%)</div><div class="kval">{var_95:.2f}%</div>
            <div class="ksub">Daily worst-case loss</div></div>
        </div>""", unsafe_allow_html=True)

    # Drawdown chart
    st.markdown('<div class="slabel">Drawdown Chart</div>', unsafe_allow_html=True)
    dd_series = drawdown * 100
    dd_dates  = df["Date"].iloc[len(df) - len(dd_series):]

    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=dd_dates, y=dd_series,
        fill="tozeroy",
        fillcolor=f"{'rgba(255,51,85,.15)' if DARK else 'rgba(204,17,51,.1)'}",
        line=dict(color=RED, width=1.5),
        name="Drawdown %",
    ))
    fig_dd.add_hline(y=max_drawdown, line_color=AMBER, line_dash="dash",
                     line_width=1, annotation_text=f"Max {max_drawdown:.1f}%",
                     annotation_font_color=AMBER, annotation_font_size=10)
    th(fig_dd, h=220, title="Portfolio Drawdown (%)")
    st.plotly_chart(fig_dd, use_container_width=True, config={"displayModeBar": False})

    # ── Support & Resistance ──────────────────────────────────────────────────
    st.markdown('<div class="slabel">Support & Resistance Levels</div>', unsafe_allow_html=True)

    def find_sr_levels(df, window=20, n_levels=5):
        highs  = df["High"].rolling(window, center=True).max()
        lows   = df["Low"].rolling(window, center=True).min()
        resist = sorted(highs.dropna().nlargest(n_levels * 3).unique())
        supp   = sorted(lows.dropna().nsmallest(n_levels * 3).unique())
        # Cluster nearby levels
        def cluster(levels, tol=0.015):
            if not list(levels): return []
            clustered, group = [], [levels[0]]
            for lv in levels[1:]:
                if (lv - group[-1]) / group[-1] < tol:
                    group.append(lv)
                else:
                    clustered.append(np.mean(group))
                    group = [lv]
            clustered.append(np.mean(group))
            return clustered
        return cluster(supp)[:n_levels], cluster(resist)[-n_levels:]

    supports, resistances = find_sr_levels(df)

    fig_sr = go.Figure()
    if ct == "Candlestick":
        fig_sr.add_trace(go.Candlestick(
            x=df["Date"].tail(120), open=df["Open"].tail(120),
            high=df["High"].tail(120), low=df["Low"].tail(120), close=df["Close"].tail(120),
            increasing=dict(line_color=GREEN, fillcolor=GREEN),
            decreasing=dict(line_color=RED, fillcolor=RED),
            name="Price", line_width=1, showlegend=False,
        ))
    else:
        fig_sr.add_trace(go.Scatter(
            x=df["Date"].tail(120), y=df["Close"].tail(120),
            line=dict(color=ACCENT, width=2), name="Price",
        ))

    for i, s in enumerate(supports):
        fig_sr.add_hline(y=s, line_color=GREEN, line_dash="dot", line_width=1.2,
                         annotation_text=f"S{i+1}: {s:.1f}",
                         annotation_font_color=GREEN, annotation_font_size=9,
                         annotation_position="left")
    for i, r in enumerate(resistances):
        fig_sr.add_hline(y=r, line_color=RED, line_dash="dot", line_width=1.2,
                         annotation_text=f"R{i+1}: {r:.1f}",
                         annotation_font_color=RED, annotation_font_size=9,
                         annotation_position="right")

    th(fig_sr, h=400, title="Support & Resistance — Last 120 Days",
       xaxis_rangeslider_visible=False)
    st.plotly_chart(fig_sr, use_container_width=True, config={"displayModeBar": False})

    # S/R Table
    sr_rows = []
    for i, s in enumerate(supports):
        diff = ((cur - s) / cur * 100)
        sr_rows.append({"Level": f"Support {i+1}", "Price": round(s,2),
                        "Distance": f"{diff:+.1f}%", "Type": "🟢 Support"})
    for i, r in enumerate(resistances):
        diff = ((r - cur) / cur * 100)
        sr_rows.append({"Level": f"Resistance {i+1}", "Price": round(r,2),
                        "Distance": f"{diff:+.1f}%", "Type": "🔴 Resistance"})
    if sr_rows:
        st.dataframe(pd.DataFrame(sr_rows), use_container_width=True, hide_index=True)

    # ── Benchmark Comparison ──────────────────────────────────────────────────
    st.markdown('<div class="slabel">Benchmark Comparison</div>', unsafe_allow_html=True)

    benchmark = "^NSEI" if ".NS" in ticker else "^GSPC"
    bm_name   = "NIFTY 50" if ".NS" in ticker else "S&P 500"

    with st.spinner(f"Fetching {bm_name}..."):
        bm_df, _ = fetch(benchmark, period)

    fig_bm = go.Figure()
    fig_bm.add_trace(go.Scatter(
        x=df["Date"], y=df["CRet"],
        line=dict(color=ACCENT, width=2),
        name=f"{name.split()[0]} ({tot:+.1f}%)",
    ))
    if bm_df is not None and not bm_df.empty:
        bm_ret = bm_df["CRet"].iloc[-1]
        fig_bm.add_trace(go.Scatter(
            x=bm_df["Date"], y=bm_df["CRet"],
            line=dict(color=AMBER, width=2, dash="dash"),
            name=f"{bm_name} ({bm_ret:+.1f}%)",
        ))
        alpha = tot - bm_ret
        ac = "up" if alpha >= 0 else "dn"; ar5 = "▲" if alpha >= 0 else "▼"
        st.markdown(f"""<div class="krow">
          <div class="kpi nu"><div class="klabel">Stock Return</div>
            <div class="kval">{"▲" if tot>=0 else "▼"} {abs(tot):.1f}%</div></div>
          <div class="kpi wa"><div class="klabel">{bm_name} Return</div>
            <div class="kval">{"▲" if bm_ret>=0 else "▼"} {abs(bm_ret):.1f}%</div></div>
          <div class="kpi {ac}"><div class="klabel">Alpha</div>
            <div class="kval">{ar5} {abs(alpha):.1f}%</div>
            <div class="ksub">{"Outperforming" if alpha>=0 else "Underperforming"} market</div></div>
        </div>""", unsafe_allow_html=True)

    fig_bm.add_hline(y=0, line_color=BORDER, line_width=1)
    th(fig_bm, h=350, title=f"{name.split()[0]} vs {bm_name} — {period}")
    st.plotly_chart(fig_bm, use_container_width=True, config={"displayModeBar": False})

    # ── Export Data ───────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Export Data</div>', unsafe_allow_html=True)

    export_cols = ["Date","Open","High","Low","Close","Volume",
                   "MA20","MA50","MA200","RSI","MACD","MACDs","V20","CRet"]
    df_export = df[[c for c in export_cols if c in df.columns]].copy()
    df_export["Date"] = df_export["Date"].astype(str)

    c1, c2 = st.columns(2)
    with c1:
        csv_data = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv_data,
            file_name=f"{ticker}_{period}_data.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        import io
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Price Data")
            # Risk metrics sheet
            risk_df = pd.DataFrame([{
                "Metric": "Sharpe Ratio",     "Value": round(sharpe, 3)},
                {"Metric": "Sortino Ratio",   "Value": round(sortino, 3)},
                {"Metric": "Max Drawdown %",  "Value": round(max_drawdown, 2)},
                {"Metric": "Ann. Return %",   "Value": round(ann_return, 2)},
                {"Metric": "Ann. Volatility %","Value": round(ann_vol, 2)},
                {"Metric": "Win Rate %",       "Value": round(win_rate, 2)},
                {"Metric": "VaR 95% %",        "Value": round(var_95, 3)},
                {"Metric": "Calmar Ratio",     "Value": round(calmar, 3)},
            ])
            risk_df.to_excel(writer, index=False, sheet_name="Risk Metrics")
        st.download_button(
            label="⬇️ Download as Excel",
            data=buf.getvalue(),
            file_name=f"{ticker}_{period}_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 6 — NEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T6:
    st.markdown(f'<div class="slabel">Latest News — {name}</div>', unsafe_allow_html=True)

    # News CSS
    st.markdown(f"""
    <style>
    .news-card {{
        background:{SURFACE}; border:1px solid {BORDER};
        border-left:3px solid {ACCENT}; border-radius:0 6px 6px 0;
        padding:16px 18px; margin-bottom:10px;
        box-shadow:{"0 2px 8px rgba(0,0,0,0.25)" if DARK else "0 1px 5px rgba(80,80,160,0.07)"};
    }}
    .news-card.pos {{ border-left-color:{GREEN}; }}
    .news-card.neg {{ border-left-color:{RED};   }}
    .news-card.neu {{ border-left-color:{ACCENT};}}
    .news-title {{
        font-family:'Syne',sans-serif; font-size:.95rem;
        font-weight:600; color:{HEAD}; line-height:1.4; margin-bottom:6px;
    }}
    .news-title a {{ color:{HEAD}; text-decoration:none; }}
    .news-title a:hover {{ color:{ACCENT}; }}
    .news-meta {{
        font-family:'IBM Plex Mono',monospace;
        font-size:.6rem; color:{MUTED}; letter-spacing:.08em;
        display:flex; gap:16px; margin-bottom:8px;
    }}
    .news-summary {{ font-size:.82rem; color:{TEXT}; line-height:1.65; }}
    .news-tag {{
        display:inline-block; font-family:'IBM Plex Mono',monospace;
        font-size:.55rem; padding:2px 8px; border-radius:3px;
        letter-spacing:.08em; text-transform:uppercase; margin-left:8px;
    }}
    .tag-pos {{ background:{"rgba(0,204,102,.15)" if DARK else "rgba(0,136,68,.1)"}; color:{GREEN}; }}
    .tag-neg {{ background:{"rgba(255,51,85,.15)"  if DARK else "rgba(204,17,51,.1)"}; color:{RED};   }}
    .tag-neu {{ background:{"rgba(91,127,255,.15)" if DARK else "rgba(51,85,238,.1)"}; color:{ACCENT};}}
    </style>
    """, unsafe_allow_html=True)

    @st.cache_data(ttl=600)
    def fetch_news(tkr):
        try:
            t = yf.Ticker(tkr)
            return t.news if hasattr(t, 'news') else []
        except:
            return []

    # Keywords for basic sentiment
    POS_WORDS = ["surge","gain","profit","beat","record","growth","rise","up","rally",
                 "strong","bullish","upgrade","buy","outperform","revenue","positive"]
    NEG_WORDS = ["fall","drop","loss","miss","decline","down","cut","bearish","downgrade",
                 "sell","underperform","risk","concern","weak","crash","plunge"]

    def sentiment(text):
        text = text.lower()
        pos = sum(1 for w in POS_WORDS if w in text)
        neg = sum(1 for w in NEG_WORDS if w in text)
        if pos > neg:   return "pos", "Positive"
        elif neg > pos: return "neg", "Negative"
        else:           return "neu", "Neutral"

    with st.spinner("Fetching latest news..."):
        news = fetch_news(ticker)

    if not news:
        st.info("No news available for this ticker right now. Try a different stock.")
    else:
        # Summary bar
        sentiments = [sentiment(n.get("title",""))[0] for n in news]
        pos_count  = sentiments.count("pos")
        neg_count  = sentiments.count("neg")
        neu_count  = sentiments.count("neu")

        st.markdown(f"""
        <div class="krow">
          <div class="kpi nu"><div class="klabel">Total Articles</div><div class="kval">{len(news)}</div><div class="ksub">Last 24–48 hrs</div></div>
          <div class="kpi up"><div class="klabel">Positive</div><div class="kval">{pos_count}</div><div class="ksub">Bullish sentiment</div></div>
          <div class="kpi dn"><div class="klabel">Negative</div><div class="kval">{neg_count}</div><div class="ksub">Bearish sentiment</div></div>
          <div class="kpi wa"><div class="klabel">Neutral</div><div class="kval">{neu_count}</div><div class="ksub">No clear signal</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        for article in news[:15]:
            title     = article.get("title", "No title")
            link      = article.get("link", "#")
            publisher = article.get("publisher", "Unknown")
            pub_time  = article.get("providerPublishTime", None)
            summary   = article.get("summary", "")

            # Format time
            if pub_time:
                try:
                    dt  = datetime.datetime.fromtimestamp(pub_time)
                    time_str = dt.strftime("%d %b %Y · %H:%M")
                    # How long ago
                    diff = datetime.datetime.now() - dt
                    hrs  = int(diff.total_seconds() / 3600)
                    ago  = f"{hrs}h ago" if hrs < 24 else f"{diff.days}d ago"
                except:
                    time_str = ""; ago = ""
            else:
                time_str = ""; ago = ""

            cls, sent_label = sentiment(title)
            tag_cls = f"tag-{cls}"

            st.markdown(f"""
            <div class="news-card {cls}">
              <div class="news-title">
                <a href="{link}" target="_blank">{title}</a>
                <span class="news-tag {tag_cls}">{sent_label}</span>
              </div>
              <div class="news-meta">
                <span>📰 {publisher}</span>
                <span>🕐 {time_str}</span>
                <span>{ago}</span>
              </div>
              {"<div class='news-summary'>" + summary[:200] + ("..." if len(summary)>200 else "") + "</div>" if summary else ""}
            </div>
            """, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 8 — PATTERNS & TOOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T8:

    # ════════════════════════════════════════════════
    # SECTION 1 — CANDLESTICK PATTERN RECOGNITION
    # ════════════════════════════════════════════════
    st.markdown('<div class="slabel">🕯️ Candlestick Pattern Recognition</div>', unsafe_allow_html=True)

    def detect_patterns(df):
        """Detect common candlestick patterns"""
        patterns = []
        d = df.copy()
        d["Body"]      = abs(d["Close"] - d["Open"])
        d["UpperWick"] = d["High"] - d[["Close","Open"]].max(axis=1)
        d["LowerWick"] = d[["Close","Open"]].min(axis=1) - d["Low"]
        d["Range"]     = d["High"] - d["Low"]
        d["IsBull"]    = d["Close"] > d["Open"]

        for i in range(2, len(d)):
            row   = d.iloc[i]
            prev  = d.iloc[i-1]
            prev2 = d.iloc[i-2]
            date  = d["Date"].iloc[i]
            close = row["Close"]

            body  = row["Body"]
            rng   = row["Range"] if row["Range"] > 0 else 1
            upper = row["UpperWick"]
            lower = row["LowerWick"]

            # ── Doji (indecision)
            if body / rng < 0.1 and rng > 0:
                patterns.append({
                    "Date": date, "Pattern": "Doji",
                    "Type": "⚪ Neutral", "Signal": "Indecision — trend may reverse",
                    "Close": close, "Strength": "Medium"
                })

            # ── Hammer (bullish reversal)
            elif (lower > 2 * body and upper < body * 0.3
                  and row["IsBull"] and prev["Close"] < prev2["Close"]):
                patterns.append({
                    "Date": date, "Pattern": "Hammer 🔨",
                    "Type": "🟢 Bullish", "Signal": "Strong bullish reversal signal",
                    "Close": close, "Strength": "Strong"
                })

            # ── Shooting Star (bearish reversal)
            elif (upper > 2 * body and lower < body * 0.3
                  and not row["IsBull"] and prev["Close"] > prev2["Close"]):
                patterns.append({
                    "Date": date, "Pattern": "Shooting Star ⭐",
                    "Type": "🔴 Bearish", "Signal": "Bearish reversal at resistance",
                    "Close": close, "Strength": "Strong"
                })

            # ── Bullish Engulfing
            elif (row["IsBull"] and not prev["IsBull"]
                  and row["Open"] < prev["Close"]
                  and row["Close"] > prev["Open"]):
                patterns.append({
                    "Date": date, "Pattern": "Bullish Engulfing",
                    "Type": "🟢 Bullish", "Signal": "Bulls overpowered bears — uptrend likely",
                    "Close": close, "Strength": "Very Strong"
                })

            # ── Bearish Engulfing
            elif (not row["IsBull"] and prev["IsBull"]
                  and row["Open"] > prev["Close"]
                  and row["Close"] < prev["Open"]):
                patterns.append({
                    "Date": date, "Pattern": "Bearish Engulfing",
                    "Type": "🔴 Bearish", "Signal": "Bears overpowered bulls — downtrend likely",
                    "Close": close, "Strength": "Very Strong"
                })

            # ── Morning Star (bullish)
            elif (not prev2["IsBull"] and prev["Body"]/rng < 0.15
                  and row["IsBull"] and row["Close"] > (prev2["Open"] + prev2["Close"]) / 2):
                patterns.append({
                    "Date": date, "Pattern": "Morning Star 🌅",
                    "Type": "🟢 Bullish", "Signal": "3-candle bullish reversal pattern",
                    "Close": close, "Strength": "Very Strong"
                })

            # ── Evening Star (bearish)
            elif (prev2["IsBull"] and prev["Body"]/rng < 0.15
                  and not row["IsBull"] and row["Close"] < (prev2["Open"] + prev2["Close"]) / 2):
                patterns.append({
                    "Date": date, "Pattern": "Evening Star 🌆",
                    "Type": "🔴 Bearish", "Signal": "3-candle bearish reversal pattern",
                    "Close": close, "Strength": "Very Strong"
                })

            # ── Marubozu (strong momentum)
            elif body / rng > 0.9:
                ptype = "🟢 Bullish" if row["IsBull"] else "🔴 Bearish"
                patterns.append({
                    "Date": date, "Pattern": f"Marubozu {'Bull' if row['IsBull'] else 'Bear'}",
                    "Type": ptype, "Signal": "Strong momentum — no wicks",
                    "Close": close, "Strength": "Strong"
                })

        return patterns

    with st.spinner("Detecting patterns..."):
        all_patterns = detect_patterns(df)

    if not all_patterns:
        st.info("No strong patterns detected in this period.")
    else:
        pat_df = pd.DataFrame(all_patterns).tail(20)

        # Summary
        bull_count = sum(1 for p in all_patterns if "Bullish" in p["Type"])
        bear_count = sum(1 for p in all_patterns if "Bearish" in p["Type"])
        neu_count  = sum(1 for p in all_patterns if "Neutral" in p["Type"])
        recent_pat = all_patterns[-1]

        st.markdown(f"""<div class="krow">
          <div class="kpi nu"><div class="klabel">Total Patterns</div>
            <div class="kval">{len(all_patterns)}</div><div class="ksub">Detected in {period}</div></div>
          <div class="kpi up"><div class="klabel">Bullish Patterns</div>
            <div class="kval">{bull_count}</div><div class="ksub">Buy signals</div></div>
          <div class="kpi dn"><div class="klabel">Bearish Patterns</div>
            <div class="kval">{bear_count}</div><div class="ksub">Sell signals</div></div>
          <div class="kpi wa"><div class="klabel">Latest Pattern</div>
            <div class="kval" style="font-size:.85rem">{recent_pat["Pattern"]}</div>
            <div class="ksub">{recent_pat["Type"]}</div></div>
        </div>""", unsafe_allow_html=True)

        # Pattern on Chart
        st.markdown('<div class="slabel">Patterns on Chart — Last 60 Days</div>', unsafe_allow_html=True)
        df60 = df.tail(60)
        fig_pat = go.Figure()
        fig_pat.add_trace(go.Candlestick(
            x=df60["Date"], open=df60["Open"], high=df60["High"],
            low=df60["Low"], close=df60["Close"],
            increasing=dict(line_color=GREEN, fillcolor=GREEN),
            decreasing=dict(line_color=RED,   fillcolor=RED),
            name="Price", line_width=1,
        ))

        # Plot pattern markers
        bull_pats = [p for p in all_patterns if "Bullish" in p["Type"] and p["Date"] >= df60["Date"].iloc[0]]
        bear_pats = [p for p in all_patterns if "Bearish" in p["Type"] and p["Date"] >= df60["Date"].iloc[0]]
        neut_pats = [p for p in all_patterns if "Neutral" in p["Type"] and p["Date"] >= df60["Date"].iloc[0]]

        if bull_pats:
            fig_pat.add_trace(go.Scatter(
                x=[p["Date"] for p in bull_pats],
                y=[p["Close"] * 0.985 for p in bull_pats],
                mode="markers+text",
                marker=dict(symbol="triangle-up", size=12, color=GREEN),
                text=[p["Pattern"].split()[0] for p in bull_pats],
                textposition="bottom center", textfont=dict(size=8, color=GREEN),
                name="Bullish Pattern",
            ))
        if bear_pats:
            fig_pat.add_trace(go.Scatter(
                x=[p["Date"] for p in bear_pats],
                y=[p["Close"] * 1.015 for p in bear_pats],
                mode="markers+text",
                marker=dict(symbol="triangle-down", size=12, color=RED),
                text=[p["Pattern"].split()[0] for p in bear_pats],
                textposition="top center", textfont=dict(size=8, color=RED),
                name="Bearish Pattern",
            ))
        if neut_pats:
            fig_pat.add_trace(go.Scatter(
                x=[p["Date"] for p in neut_pats],
                y=[p["Close"] for p in neut_pats],
                mode="markers",
                marker=dict(symbol="circle", size=8, color=AMBER),
                name="Neutral Pattern",
            ))

        th(fig_pat, h=420, title="Candlestick Patterns — Last 60 Days",
           xaxis_rangeslider_visible=False)
        st.plotly_chart(fig_pat, use_container_width=True, config={"displayModeBar": False})

        # Pattern Table
        st.markdown('<div class="slabel">Recent Patterns (Last 20)</div>', unsafe_allow_html=True)
        display_df = pat_df[["Date","Pattern","Type","Signal","Close","Strength"]].copy()
        display_df["Date"] = display_df["Date"].astype(str).str[:10]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════
    # SECTION 2 — VOLUME ANALYSIS
    # ════════════════════════════════════════════════
    st.markdown('<div class="slabel">📊 Volume Analysis — OBV & Spike Detection</div>', unsafe_allow_html=True)

    # OBV — On Balance Volume
    obv = [0]
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["Close"].iloc[i-1]:
            obv.append(obv[-1] + df["Volume"].iloc[i])
        elif df["Close"].iloc[i] < df["Close"].iloc[i-1]:
            obv.append(obv[-1] - df["Volume"].iloc[i])
        else:
            obv.append(obv[-1])
    df["OBV"] = obv

    # Volume spike — 2x average
    vol_avg      = df["Volume"].rolling(20).mean()
    df["VolSpike"] = df["Volume"] > vol_avg * 2

    spike_count = df["VolSpike"].sum()
    avg_vol_val = df["Volume"].mean()
    max_vol_val = df["Volume"].max()

    st.markdown(f"""<div class="krow">
      <div class="kpi nu"><div class="klabel">Avg Daily Volume</div>
        <div class="kval">{avg_vol_val/1e6:.1f}M</div></div>
      <div class="kpi wa"><div class="klabel">Max Volume Day</div>
        <div class="kval">{max_vol_val/1e6:.1f}M</div></div>
      <div class="kpi {'up' if spike_count>0 else 'nu'}"><div class="klabel">Volume Spikes</div>
        <div class="kval">{spike_count}</div>
        <div class="ksub">Days with 2x avg volume</div></div>
      <div class="kpi {'up' if obv[-1]>0 else 'dn'}"><div class="klabel">OBV Trend</div>
        <div class="kval">{"Rising ▲" if obv[-1]>obv[len(obv)//2] else "Falling ▼"}</div>
        <div class="ksub">On Balance Volume</div></div>
    </div>""", unsafe_allow_html=True)

    # OBV Chart
    fig_obv = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.5, 0.5], vertical_spacing=0.04)

    # Price
    fig_obv.add_trace(go.Scatter(
        x=df["Date"], y=df["Close"],
        line=dict(color=ACCENT, width=1.8), name="Price",
    ), row=1, col=1)

    # Volume bars with spikes highlighted
    vol_colors = []
    for i, row in df.iterrows():
        if df.loc[i, "VolSpike"]:
            vol_colors.append(AMBER)
        elif row["Close"] >= row["Open"]:
            vol_colors.append(GREEN)
        else:
            vol_colors.append(RED)

    fig_obv.add_trace(go.Bar(
        x=df["Date"], y=df["Volume"],
        marker_color=vol_colors, name="Volume", opacity=0.6,
    ), row=2, col=1)

    # OBV line on volume chart (normalized)
    obv_series = pd.Series(obv)
    obv_norm = (obv_series - obv_series.min()) / (obv_series.max() - obv_series.min()) * df["Volume"].max()
    fig_obv.add_trace(go.Scatter(
        x=df["Date"], y=obv_norm,
        line=dict(color="#9944ff", width=2, dash="dot"),
        name="OBV (scaled)",
    ), row=2, col=1)

    th(fig_obv, h=400, title="Price + Volume Analysis (🟡 = Volume Spike)")
    fig_obv.update_yaxes(title_text="Price",  row=1, col=1, title_font_color=MUTED)
    fig_obv.update_yaxes(title_text="Volume", row=2, col=1, title_font_color=MUTED)
    st.plotly_chart(fig_obv, use_container_width=True, config={"displayModeBar": False})

    # Volume spike dates table
    spike_dates = df[df["VolSpike"]][["Date","Close","Volume"]].tail(10).copy()
    if not spike_dates.empty:
        spike_dates["Date"]   = spike_dates["Date"].astype(str).str[:10]
        spike_dates["Volume"] = spike_dates["Volume"].apply(lambda x: f"{x/1e6:.2f}M")
        st.markdown('<div class="slabel">Recent Volume Spikes (Last 10)</div>', unsafe_allow_html=True)
        st.dataframe(spike_dates, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════
    # SECTION 3 — PRICE TARGET & RISK/REWARD
    # ════════════════════════════════════════════════
    st.markdown('<div class="slabel">🎯 Price Target & Risk/Reward Calculator</div>', unsafe_allow_html=True)
    st.caption("Enter your trade details to calculate Risk/Reward ratio")

    c1, c2, c3 = st.columns(3)
    with c1:
        entry_price = st.number_input(
            "Entry Price", value=float(round(cur, 2)),
            min_value=0.01, step=0.5,
            help="Price at which you plan to buy"
        )
    with c2:
        stop_loss = st.number_input(
            "Stop Loss", value=float(round(cur * 0.95, 2)),
            min_value=0.01, step=0.5,
            help="Price at which you'll exit if wrong"
        )
    with c3:
        target = st.number_input(
            "Target Price", value=float(round(cur * 1.10, 2)),
            min_value=0.01, step=0.5,
            help="Price at which you'll book profit"
        )

    qty_input = st.number_input("Quantity (shares)", value=10, min_value=1, step=1)

    if entry_price > 0 and stop_loss > 0 and target > 0:
        risk_per_share   = entry_price - stop_loss
        reward_per_share = target - entry_price
        rr_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else 0

        total_risk   = risk_per_share * qty_input
        total_reward = reward_per_share * qty_input
        total_invest = entry_price * qty_input
        risk_pct     = (risk_per_share / entry_price) * 100
        reward_pct   = (reward_per_share / entry_price) * 100

        rr_color = "up" if rr_ratio >= 2 else "wa" if rr_ratio >= 1 else "dn"
        rr_label = "Excellent ✅" if rr_ratio >= 3 else "Good ✅" if rr_ratio >= 2 else "Acceptable ⚠️" if rr_ratio >= 1 else "Poor ❌"

        st.markdown(f"""<div class="krow">
          <div class="kpi nu"><div class="klabel">Total Investment</div>
            <div class="kval">₹{total_invest:,.0f}</div>
            <div class="ksub">{qty_input} shares @ {entry_price}</div></div>
          <div class="kpi dn"><div class="klabel">Max Risk</div>
            <div class="kval">₹{total_risk:,.0f}</div>
            <div class="ksub">▼ {risk_pct:.1f}% per share</div></div>
          <div class="kpi up"><div class="klabel">Potential Reward</div>
            <div class="kval">₹{total_reward:,.0f}</div>
            <div class="ksub">▲ {reward_pct:.1f}% per share</div></div>
          <div class="kpi {rr_color}"><div class="klabel">Risk:Reward Ratio</div>
            <div class="kval">1 : {rr_ratio:.1f}</div>
            <div class="ksub">{rr_label}</div></div>
        </div>""", unsafe_allow_html=True)

        # Visual R:R chart
        fig_rr = go.Figure()

        # Price line
        fig_rr.add_trace(go.Scatter(
            x=df["Date"].tail(60), y=df["Close"].tail(60),
            line=dict(color=ACCENT, width=1.5), name="Price", opacity=0.7,
        ))

        # Entry, Stop Loss, Target lines
        fig_rr.add_hline(y=entry_price, line_color=AMBER, line_width=2,
                         annotation_text=f"Entry: {entry_price:.1f}",
                         annotation_font_color=AMBER, annotation_font_size=10)
        fig_rr.add_hline(y=stop_loss, line_color=RED, line_width=2, line_dash="dash",
                         annotation_text=f"Stop Loss: {stop_loss:.1f} (-{risk_pct:.1f}%)",
                         annotation_font_color=RED, annotation_font_size=10)
        fig_rr.add_hline(y=target, line_color=GREEN, line_width=2, line_dash="dash",
                         annotation_text=f"Target: {target:.1f} (+{reward_pct:.1f}%)",
                         annotation_font_color=GREEN, annotation_font_size=10)

        # Fill zones
        fig_rr.add_hrect(y0=stop_loss, y1=entry_price,
                         fillcolor=f"{'rgba(255,51,85,.1)' if DARK else 'rgba(204,17,51,.08)'}",
                         annotation_text="Risk Zone", annotation_font_color=RED,
                         annotation_font_size=9)
        fig_rr.add_hrect(y0=entry_price, y1=target,
                         fillcolor=f"{'rgba(0,204,102,.1)' if DARK else 'rgba(0,136,68,.08)'}",
                         annotation_text="Reward Zone", annotation_font_color=GREEN,
                         annotation_font_size=9)

        th(fig_rr, h=380, title=f"Trade Setup — R:R = 1:{rr_ratio:.1f}")
        st.plotly_chart(fig_rr, use_container_width=True, config={"displayModeBar": False})

        # Breakeven & Win probability
        st.markdown('<div class="slabel">Breakeven Analysis</div>', unsafe_allow_html=True)
        breakeven_winrate = 1 / (1 + rr_ratio) * 100 if rr_ratio > 0 else 50

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="sig bl">
                <strong>Minimum Win Rate Needed: {breakeven_winrate:.1f}%</strong><br>
                To be profitable with 1:{rr_ratio:.1f} R:R, you need to win at least {breakeven_winrate:.1f}% of your trades.
            </div>""", unsafe_allow_html=True)
        with c2:
            trades_to_recover = int(np.ceil(total_risk / total_reward)) if total_reward > 0 else 0
            st.markdown(f"""<div class="sig {'bl' if rr_ratio>=2 else 'bn'}">
                <strong>Trades to recover 1 loss: {trades_to_recover}</strong><br>
                {"Great R:R! One win recovers multiple losses." if rr_ratio>=2 else "Consider improving R:R above 1:2 for consistent profitability."}
            </div>""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 9 — ML PRICE FORECAST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T9:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import r2_score, mean_absolute_error
    import warnings
    warnings.filterwarnings("ignore")

    st.markdown('<div class="slabel">🤖 ML Price Prediction — Next 30 Days</div>', unsafe_allow_html=True)
    st.caption("Models trained on historical OHLCV + technical indicators. For educational purposes only.")

    # ── Settings ──────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        forecast_days = st.slider("Forecast Days", min_value=7, max_value=60, value=30, step=7)
    with c2:
        model_choice = st.radio("Model", ["Linear Regression", "Random Forest", "Both"], horizontal=True)

    # ── Feature Engineering for ML ────────────────────────────────────────────
    def prepare_features(df):
        d = df.copy().dropna()
        d["Day"]       = np.arange(len(d))
        d["MA5"]       = d["Close"].rolling(5).mean()
        d["MA10"]      = d["Close"].rolling(10).mean()
        d["MA20"]      = d["Close"].rolling(20).mean()
        d["STD10"]     = d["Close"].rolling(10).std()
        d["MOM5"]      = d["Close"].diff(5)
        d["MOM10"]     = d["Close"].diff(10)
        d["ROC5"]      = d["Close"].pct_change(5) * 100
        d["HL_Ratio"]  = (d["High"] - d["Low"]) / d["Close"]
        d["OC_Ratio"]  = (d["Close"] - d["Open"]) / d["Open"]
        d["Vol_MA10"]  = d["Volume"].rolling(10).mean()
        d["RSI"]       = d["RSI"] if "RSI" in d.columns else 50
        d = d.dropna()
        features = ["Day","MA5","MA10","MA20","STD10","MOM5","MOM10",
                    "ROC5","HL_Ratio","OC_Ratio","Vol_MA10","RSI"]
        return d, features

    def run_lr(df, forecast_days):
        d, feats = prepare_features(df)
        X = d[feats].values
        y = d["Close"].values

        scaler_x = MinMaxScaler()
        scaler_y = MinMaxScaler()
        X_sc = scaler_x.fit_transform(X)
        y_sc = scaler_y.fit_transform(y.reshape(-1,1)).ravel()

        # Train on 80%
        split   = int(len(X_sc) * 0.8)
        X_train, X_test = X_sc[:split], X_sc[split:]
        y_train, y_test = y_sc[:split], y_sc[split:]

        model = LinearRegression()
        model.fit(X_train, y_train)

        # Test metrics
        y_pred_test = model.predict(X_test)
        y_pred_inv  = scaler_y.inverse_transform(y_pred_test.reshape(-1,1)).ravel()
        y_test_inv  = scaler_y.inverse_transform(y_test.reshape(-1,1)).ravel()
        r2  = r2_score(y_test_inv, y_pred_inv)
        mae = mean_absolute_error(y_test_inv, y_pred_inv)

        # Full prediction
        y_all_pred = scaler_y.inverse_transform(model.predict(X_sc).reshape(-1,1)).ravel()

        # Future forecast
        last_day   = d["Day"].iloc[-1]
        last_feats = d[feats].iloc[-1].copy()
        future_preds = []
        for i in range(1, forecast_days + 1):
            last_feats["Day"] = last_day + i
            x_fut = scaler_x.transform(last_feats.values.reshape(1,-1))
            pred  = scaler_y.inverse_transform(model.predict(x_fut).reshape(-1,1))[0,0]
            future_preds.append(pred)
            last_feats["MA5"] = np.mean([pred] + list(future_preds[-4:]))

        future_dates = pd.date_range(d["Date"].iloc[-1] + pd.Timedelta(days=1),
                                     periods=forecast_days, freq="B")
        return d, y_all_pred, future_dates, future_preds, r2, mae

    def run_rf(df, forecast_days):
        d, feats = prepare_features(df)
        X = d[feats].values
        y = d["Close"].values

        split   = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        y_pred_test = model.predict(X_test)
        r2  = r2_score(y_test, y_pred_test)
        mae = mean_absolute_error(y_test, y_pred_test)
        y_all_pred = model.predict(X)

        # Future forecast
        last_feats = d[feats].iloc[-1].copy()
        last_day   = d["Day"].iloc[-1]
        future_preds = []
        for i in range(1, forecast_days + 1):
            last_feats["Day"] = last_day + i
            pred = model.predict(last_feats.values.reshape(1,-1))[0]
            future_preds.append(pred)
            last_feats["MA5"] = np.mean([pred] + list(future_preds[-4:]))

        future_dates = pd.date_range(d["Date"].iloc[-1] + pd.Timedelta(days=1),
                                     periods=forecast_days, freq="B")

        # Feature importance
        importance = pd.DataFrame({
            "Feature": feats,
            "Importance": model.feature_importances_
        }).sort_values("Importance", ascending=False)

        return d, y_all_pred, future_dates, future_preds, r2, mae, importance

    # ── Run Models ────────────────────────────────────────────────────────────
    with st.spinner("Training ML models... ⏳"):
        results = {}
        if model_choice in ["Linear Regression", "Both"]:
            d_lr, pred_lr, fdates_lr, fpreds_lr, r2_lr, mae_lr = run_lr(df, forecast_days)
            results["Linear Regression"] = {
                "d": d_lr, "all_pred": pred_lr, "fdates": fdates_lr,
                "fpreds": fpreds_lr, "r2": r2_lr, "mae": mae_lr,
                "color": ACCENT
            }
        if model_choice in ["Random Forest", "Both"]:
            d_rf, pred_rf, fdates_rf, fpreds_rf, r2_rf, mae_rf, feat_imp = run_rf(df, forecast_days)
            results["Random Forest"] = {
                "d": d_rf, "all_pred": pred_rf, "fdates": fdates_rf,
                "fpreds": fpreds_rf, "r2": r2_rf, "mae": mae_rf,
                "color": GREEN
            }

    # ── Model Metrics ─────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Model Performance</div>', unsafe_allow_html=True)

    metric_cols = st.columns(len(results) * 2)
    col_idx = 0
    for mname, res in results.items():
        r2_col = "up" if res["r2"] > 0.85 else "wa" if res["r2"] > 0.7 else "dn"
        with metric_cols[col_idx]:
            st.markdown(f"""<div class="kpi nu">
                <div class="klabel">{mname}</div>
                <div class="kval" style="font-size:.9rem">{mname.split()[0]}</div>
            </div>""", unsafe_allow_html=True)
        with metric_cols[col_idx + 1]:
            st.markdown(f"""<div class="kpi {r2_col}">
                <div class="klabel">R² Score</div>
                <div class="kval">{res['r2']:.3f}</div>
                <div class="ksub">MAE: {res['mae']:.2f} · {"Excellent" if res['r2']>0.85 else "Good" if res['r2']>0.7 else "Fair"}</div>
            </div>""", unsafe_allow_html=True)
        col_idx += 2

    # ── Forecast Chart ────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Price Forecast Chart</div>', unsafe_allow_html=True)

    fig_ml = go.Figure()

    # Actual price
    first_res = list(results.values())[0]
    d_base    = first_res["d"]

    fig_ml.add_trace(go.Scatter(
        x=d_base["Date"], y=d_base["Close"],
        line=dict(color=TEXT, width=1.5),
        name="Actual Price", opacity=0.8,
    ))

    # Model predictions + forecast
    for mname, res in results.items():
        # Historical fit
        fig_ml.add_trace(go.Scatter(
            x=res["d"]["Date"], y=res["all_pred"],
            line=dict(color=res["color"], width=1.2, dash="dot"),
            name=f"{mname} (fit)", opacity=0.6,
        ))

        # Future forecast
        fig_ml.add_trace(go.Scatter(
            x=res["fdates"], y=res["fpreds"],
            line=dict(color=res["color"], width=2.5, dash="dash"),
            name=f"{mname} Forecast ({forecast_days}D)",
            mode="lines+markers",
            marker=dict(size=5),
        ))

        # Confidence band (±5% of forecast)
        upper = [p * 1.05 for p in res["fpreds"]]
        lower = [p * 0.95 for p in res["fpreds"]]
        fig_ml.add_trace(go.Scatter(
            x=list(res["fdates"]) + list(res["fdates"])[::-1],
            y=upper + lower[::-1],
            fill="toself",
            fillcolor=f"{'rgba(91,127,255,.08)' if res['color']==ACCENT else 'rgba(0,204,102,.08)'}",
            line=dict(color="rgba(0,0,0,0)"),
            name=f"{mname} ±5% CI",
            showlegend=True,
        ))

    # Vertical line — forecast start
    last_date = d_base["Date"].iloc[-1]
    fig_ml.add_shape(type="line",
        x0=last_date, x1=last_date, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color=AMBER, dash="dash", width=1.5),
    )
    fig_ml.add_annotation(
        x=last_date, y=1, xref="x", yref="paper",
        text="Forecast →", showarrow=False,
        font=dict(color=AMBER, size=10), xanchor="left",
    )

    th(fig_ml, h=500, title=f"ML Price Forecast — Next {forecast_days} Trading Days")
    st.plotly_chart(fig_ml, use_container_width=True, config={"displayModeBar": False})

    # ── Forecast Table ────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Forecast Values</div>', unsafe_allow_html=True)

    forecast_table = {"Date": [str(d.date()) for d in list(results.values())[0]["fdates"]]}
    for mname, res in results.items():
        forecast_table[f"{mname} Price"] = [round(p, 2) for p in res["fpreds"]]
        forecast_table[f"{mname} Change%"] = [
            f"{((p - cur) / cur * 100):+.2f}%" for p in res["fpreds"]
        ]

    ft_df = pd.DataFrame(forecast_table)
    st.dataframe(ft_df, use_container_width=True, hide_index=True)

    # ── 30D Target Summary ────────────────────────────────────────────────────
    st.markdown('<div class="slabel">30-Day Price Target Summary</div>', unsafe_allow_html=True)

    sum_cols = st.columns(len(results))
    for i, (mname, res) in enumerate(results.items()):
        final_pred = res["fpreds"][-1]
        chg        = ((final_pred - cur) / cur * 100)
        col_c      = "up" if chg >= 0 else "dn"
        ar         = "▲" if chg >= 0 else "▼"
        with sum_cols[i]:
            st.markdown(f"""<div class="kpi {col_c}">
                <div class="klabel">{mname} — Day {forecast_days} Target</div>
                <div class="kval">{final_pred:.2f}</div>
                <div class="ksub">{ar} {abs(chg):.1f}% from current {cur:.2f}</div>
            </div>""", unsafe_allow_html=True)

    # ── Feature Importance (RF only) ──────────────────────────────────────────
    if "Random Forest" in results:
        st.markdown('<div class="slabel">Feature Importance — Random Forest</div>', unsafe_allow_html=True)
        fig_fi = go.Figure(go.Bar(
            x=feat_imp["Importance"],
            y=feat_imp["Feature"],
            orientation="h",
            marker_color=PALETTE[:len(feat_imp)],
        ))
        th(fig_fi, h=320, title="Which features matter most for prediction?")
        st.plotly_chart(fig_fi, use_container_width=True, config={"displayModeBar": False})

    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.markdown(f"""<div class="sig bn">
        <strong>⚠️ Important Disclaimer</strong><br>
        ML models are trained on historical data and cannot predict future prices with certainty.
        Stock markets are influenced by news, sentiment, and macroeconomic factors that models cannot capture.
        This forecast is for <strong>educational purposes only</strong> — not financial advice.
    </div>""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 10 — OPTIONS CHAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T10:
    st.markdown('<div class="slabel">📈 Options Chain Analysis</div>', unsafe_allow_html=True)
    st.caption("Options data available for US stocks & some NSE stocks. Try AAPL, MSFT, TSLA, NVDA.")

    @st.cache_data(ttl=300)
    def fetch_options(tkr):
        try:
            t = yf.Ticker(tkr)
            exps = t.options
            if not exps: return None, None, None
            return t, exps, True
        except: return None, None, None

    tick_obj, expirations, has_options = fetch_options(ticker)

    if not has_options or not expirations:
        st.warning(f"⚠️ Options data not available for `{ticker}`. Try US stocks like `AAPL`, `MSFT`, `TSLA`, `NVDA`.")
    else:
        # ── Expiry selector ───────────────────────────────────────────────────
        st.markdown('<div class="slabel">Select Expiry Date</div>', unsafe_allow_html=True)
        selected_exp = st.selectbox(
            "Expiration Date",
            options=expirations[:12],
            label_visibility="collapsed"
        )

        @st.cache_data(ttl=300)
        def fetch_chain(tkr, exp):
            try:
                t     = yf.Ticker(tkr)
                chain = t.option_chain(exp)
                return chain.calls, chain.puts
            except: return None, None

        calls_df, puts_df = fetch_chain(ticker, selected_exp)

        if calls_df is None or puts_df is None:
            st.error("Could not fetch options chain. Try again.")
        else:
            # ── Clean data ────────────────────────────────────────────────────
            cols_keep = ["strike","lastPrice","bid","ask","volume","openInterest","impliedVolatility","inTheMoney"]
            calls_df  = calls_df[[c for c in cols_keep if c in calls_df.columns]].copy()
            puts_df   = puts_df[[c for c in cols_keep if c in puts_df.columns]].copy()

            calls_df["impliedVolatility"] = (calls_df["impliedVolatility"] * 100).round(2)
            puts_df["impliedVolatility"]  = (puts_df["impliedVolatility"]  * 100).round(2)
            calls_df["volume"]       = calls_df["volume"].fillna(0).astype(int)
            puts_df["volume"]        = puts_df["volume"].fillna(0).astype(int)
            calls_df["openInterest"] = calls_df["openInterest"].fillna(0).astype(int)
            puts_df["openInterest"]  = puts_df["openInterest"].fillna(0).astype(int)

            # ── Key Metrics ───────────────────────────────────────────────────
            total_call_oi = calls_df["openInterest"].sum()
            total_put_oi  = puts_df["openInterest"].sum()
            pcr_oi        = total_put_oi / total_call_oi if total_call_oi > 0 else 0

            total_call_vol = calls_df["volume"].sum()
            total_put_vol  = puts_df["volume"].sum()
            pcr_vol        = total_put_vol / total_call_vol if total_call_vol > 0 else 0

            avg_call_iv = calls_df["impliedVolatility"].mean()
            avg_put_iv  = puts_df["impliedVolatility"].mean()

            # PCR interpretation
            pcr_color = "dn" if pcr_oi > 1.2 else "up" if pcr_oi < 0.8 else "wa"
            pcr_label = "Bearish 🐻" if pcr_oi > 1.2 else "Bullish 🐂" if pcr_oi < 0.8 else "Neutral ⚖️"

            st.markdown(f"""<div class="krow">
              <div class="kpi nu"><div class="klabel">Current Price</div>
                <div class="kval">{cur:.2f}</div>
                <div class="ksub">Underlying price</div></div>
              <div class="kpi {pcr_color}"><div class="klabel">P/C Ratio (OI)</div>
                <div class="kval">{pcr_oi:.2f}</div>
                <div class="ksub">{pcr_label}</div></div>
              <div class="kpi {'dn' if pcr_vol>1 else 'up'}"><div class="klabel">P/C Ratio (Vol)</div>
                <div class="kval">{pcr_vol:.2f}</div>
                <div class="ksub">Volume based</div></div>
              <div class="kpi wa"><div class="klabel">Avg Call IV</div>
                <div class="kval">{avg_call_iv:.1f}%</div>
                <div class="ksub">Implied Volatility</div></div>
              <div class="kpi wa"><div class="klabel">Avg Put IV</div>
                <div class="kval">{avg_put_iv:.1f}%</div>
                <div class="ksub">Implied Volatility</div></div>
              <div class="kpi nu"><div class="klabel">Expiry</div>
                <div class="kval" style="font-size:.9rem">{selected_exp}</div>
                <div class="ksub">Selected expiration</div></div>
            </div>""", unsafe_allow_html=True)

            # PCR Signal
            if pcr_oi > 1.2:
                sig_cls, sig_text = "br", f"PCR = {pcr_oi:.2f} → High put buying = Bearish sentiment. Market expects downside."
            elif pcr_oi < 0.8:
                sig_cls, sig_text = "bl", f"PCR = {pcr_oi:.2f} → High call buying = Bullish sentiment. Market expects upside."
            else:
                sig_cls, sig_text = "bn", f"PCR = {pcr_oi:.2f} → Balanced market. No strong directional bias."

            st.markdown(f'<div class="sig {sig_cls}"><strong>Put/Call Signal:</strong> {sig_text}</div>',
                        unsafe_allow_html=True)

            # ── Open Interest Chart ───────────────────────────────────────────
            st.markdown('<div class="slabel">Open Interest by Strike Price</div>', unsafe_allow_html=True)

            # Filter near ATM strikes
            atm_range  = cur * 0.15
            calls_near = calls_df[(calls_df["strike"] >= cur - atm_range) &
                                   (calls_df["strike"] <= cur + atm_range)]
            puts_near  = puts_df[(puts_df["strike"]  >= cur - atm_range) &
                                  (puts_df["strike"]  <= cur + atm_range)]

            fig_oi = go.Figure()
            fig_oi.add_trace(go.Bar(
                x=calls_near["strike"], y=calls_near["openInterest"],
                name="Call OI", marker_color=GREEN, opacity=0.8,
            ))
            fig_oi.add_trace(go.Bar(
                x=puts_near["strike"], y=puts_near["openInterest"],
                name="Put OI", marker_color=RED, opacity=0.8,
            ))
            fig_oi.add_vline(
                x=cur, line_color=AMBER, line_dash="dash", line_width=2,
            )
            fig_oi.add_annotation(
                x=cur, y=1, xref="x", yref="paper",
                text=f"CMP: {cur:.1f}", showarrow=False,
                font=dict(color=AMBER, size=10), xanchor="left",
            )
            fig_oi.update_layout(barmode="group")
            th(fig_oi, h=350, title="Open Interest — Calls vs Puts (Near ATM strikes)")
            st.plotly_chart(fig_oi, use_container_width=True, config={"displayModeBar": False})

            # ── IV Smile Chart ────────────────────────────────────────────────
            st.markdown('<div class="slabel">Implied Volatility Smile</div>', unsafe_allow_html=True)
            fig_iv = go.Figure()
            fig_iv.add_trace(go.Scatter(
                x=calls_near["strike"], y=calls_near["impliedVolatility"],
                line=dict(color=GREEN, width=2),
                mode="lines+markers", marker=dict(size=6),
                name="Call IV %",
            ))
            fig_iv.add_trace(go.Scatter(
                x=puts_near["strike"], y=puts_near["impliedVolatility"],
                line=dict(color=RED, width=2),
                mode="lines+markers", marker=dict(size=6),
                name="Put IV %",
            ))
            fig_iv.add_vline(x=cur, line_color=AMBER, line_dash="dash", line_width=1.5)
            th(fig_iv, h=300, title="IV Smile — Implied Volatility across Strike Prices")
            fig_iv.update_yaxes(title_text="IV %")
            st.plotly_chart(fig_iv, use_container_width=True, config={"displayModeBar": False})

            # ── Options Chain Table ───────────────────────────────────────────
            st.markdown('<div class="slabel">Full Options Chain</div>', unsafe_allow_html=True)

            tab_calls, tab_puts = st.tabs(["📗 Calls", "📕 Puts"])

            with tab_calls:
                calls_display = calls_df.rename(columns={
                    "strike":"Strike","lastPrice":"Last Price",
                    "bid":"Bid","ask":"Ask","volume":"Volume",
                    "openInterest":"Open Interest",
                    "impliedVolatility":"IV %","inTheMoney":"ITM"
                })
                # Highlight ITM rows
                st.dataframe(
                    calls_display.style.apply(
                        lambda row: [f"background-color: {'rgba(0,204,102,.08)' if row.get('ITM', False) else ''}" for _ in row],
                        axis=1
                    ),
                    use_container_width=True, hide_index=True, height=350
                )

            with tab_puts:
                puts_display = puts_df.rename(columns={
                    "strike":"Strike","lastPrice":"Last Price",
                    "bid":"Bid","ask":"Ask","volume":"Volume",
                    "openInterest":"Open Interest",
                    "impliedVolatility":"IV %","inTheMoney":"ITM"
                })
                st.dataframe(
                    puts_display.style.apply(
                        lambda row: [f"background-color: {'rgba(255,51,85,.08)' if row.get('ITM', False) else ''}" for _ in row],
                        axis=1
                    ),
                    use_container_width=True, hide_index=True, height=350
                )

            # ── Max Pain ──────────────────────────────────────────────────────
            st.markdown('<div class="slabel">Max Pain Analysis</div>', unsafe_allow_html=True)

            try:
                all_strikes = sorted(set(calls_df["strike"].tolist() + puts_df["strike"].tolist()))
                pain = []
                for s in all_strikes:
                    call_pain = calls_df[calls_df["strike"] < s].apply(
                        lambda r: (s - r["strike"]) * r["openInterest"], axis=1).sum()
                    put_pain  = puts_df[puts_df["strike"]  > s].apply(
                        lambda r: (r["strike"] - s) * r["openInterest"], axis=1).sum()
                    pain.append(call_pain + put_pain)

                max_pain_idx   = pain.index(min(pain))
                max_pain_price = all_strikes[max_pain_idx]

                c1, c2 = st.columns(2)
                with c1:
                    mp_diff = ((max_pain_price - cur) / cur * 100)
                    mp_col  = "up" if mp_diff >= 0 else "dn"
                    ar      = "▲" if mp_diff >= 0 else "▼"
                    st.markdown(f"""<div class="kpi {mp_col}">
                        <div class="klabel">Max Pain Strike</div>
                        <div class="kval">{max_pain_price:.0f}</div>
                        <div class="ksub">{ar} {abs(mp_diff):.1f}% from CMP · Options expire worthless here</div>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class="sig {'bl' if mp_diff>=0 else 'br'}">
                        <strong>Max Pain = {max_pain_price:.0f}</strong><br>
                        Price tends to gravitate toward max pain at expiry.
                        {"Stock may rise toward " if mp_diff>=0 else "Stock may fall toward "}
                        {max_pain_price:.0f} by {selected_exp}.
                    </div>""", unsafe_allow_html=True)

                # Pain chart
                fig_pain = go.Figure()
                fig_pain.add_trace(go.Scatter(
                    x=all_strikes, y=pain,
                    line=dict(color=ACCENT, width=2),
                    fill="tozeroy",
                    fillcolor=f"{'rgba(91,127,255,.07)' if DARK else 'rgba(51,85,238,.05)'}",
                    name="Total Pain",
                ))
                fig_pain.add_vline(x=max_pain_price, line_color=GREEN, line_dash="dash", line_width=2)
                fig_pain.add_annotation(
                    x=max_pain_price, y=1, xref="x", yref="paper",
                    text=f"Max Pain: {max_pain_price:.0f}",
                    showarrow=False, font=dict(color=GREEN, size=10), xanchor="left"
                )
                fig_pain.add_vline(x=cur, line_color=AMBER, line_dash="dot", line_width=1.5)
                th(fig_pain, h=280, title="Max Pain Chart — Where options expire worthless")
                st.plotly_chart(fig_pain, use_container_width=True, config={"displayModeBar": False})
            except:
                st.info("Max pain calculation not available for this expiry.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 11 — SECTOR HEATMAP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T11:
    st.markdown('<div class="slabel">🌍 Market Sector Heatmap</div>', unsafe_allow_html=True)

    # ── Market selector ───────────────────────────────────────────────────────
    market_sel = st.radio("Market", ["🇮🇳 India (NSE)", "🇺🇸 US Market"], horizontal=True)

    # ── Sector definitions ────────────────────────────────────────────────────
    NSE_SECTORS = {
        "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS","PERSISTENT.NS","COFORGE.NS"],
        "Banking": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS","INDUSINDBK.NS","BANDHANBNK.NS"],
        "Auto": ["TATAMOTORS.NS","MARUTI.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","EICHERMOT.NS","M&M.NS","TVSMOTOR.NS"],
        "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS","APOLLOHOSP.NS","AUROPHARMA.NS"],
        "Energy": ["RELIANCE.NS","ONGC.NS","NTPC.NS","POWERGRID.NS","COALINDIA.NS","BPCL.NS","IOC.NS"],
        "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS","DABUR.NS","MARICO.NS","GODREJCP.NS"],
        "Metals": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","VEDL.NS","SAIL.NS","NMDC.NS"],
        "Infra": ["ADANIENT.NS","ADANIPORTS.NS","DLF.NS","LODHA.NS","GODREJPROP.NS","OBEROIRLTY.NS"],
        "Finance": ["BAJFINANCE.NS","BAJAJFINSV.NS","HDFC.NS","MUTHOOTFIN.NS","CHOLAFIN.NS","LICHSGFIN.NS"],
        "Telecom": ["BHARTIARTL.NS","INDUSTOWER.NS","TATACOMM.NS"],
    }

    US_SECTORS = {
        "Technology": ["AAPL","MSFT","NVDA","GOOGL","META","ORCL","ADBE","CRM"],
        "Consumer": ["AMZN","TSLA","NKE","SBUX","MCD","HD","TGT","COST"],
        "Healthcare": ["JNJ","UNH","PFE","ABBV","MRK","TMO","ABT","LLY"],
        "Finance": ["JPM","BAC","GS","MS","V","MA","BRK-B","C"],
        "Energy": ["XOM","CVX","COP","SLB","EOG","PXD","MPC","VLO"],
        "Industrials": ["CAT","BA","GE","MMM","HON","UPS","FDX","RTX"],
        "Telecom": ["T","VZ","TMUS","CMCSA","CHTR","DISH"],
        "Real Estate": ["AMT","PLD","CCI","EQIX","SPG","PSA"],
        "Utilities": ["NEE","DUK","SO","D","AEP","EXC"],
        "Materials": ["LIN","APD","SHW","ECL","NEM","FCX"],
    }

    sectors = NSE_SECTORS if "India" in market_sel else US_SECTORS

    # ── Fetch sector data ─────────────────────────────────────────────────────
    @st.cache_data(ttl=300)
    def fetch_sector_data(market, period_sel="1d"):
        sec_data = NSE_SECTORS if "India" in market else US_SECTORS
        results  = {}
        for sector, tickers_list in sec_data.items():
            sector_stocks = []
            for tk in tickers_list:
                try:
                    d = yf.Ticker(tk).history(period="5d")
                    if len(d) >= 2:
                        cur_p  = d["Close"].iloc[-1]
                        prev_p = d["Close"].iloc[-2]
                        chg    = (cur_p - prev_p) / prev_p * 100
                        mktcap = None
                        try:
                            info   = yf.Ticker(tk).info
                            mktcap = info.get("marketCap", None)
                        except: pass
                        sector_stocks.append({
                            "ticker": tk.replace(".NS",""),
                            "change": round(chg, 2),
                            "price":  round(cur_p, 2),
                            "mktcap": mktcap or 1e9,
                        })
                except: pass
            if sector_stocks:
                results[sector] = sector_stocks
        return results

    with st.spinner("Fetching sector data... (may take 30-60 seconds)"):
        sector_data = fetch_sector_data(market_sel)

    if not sector_data:
        st.error("Could not fetch sector data. Check internet connection.")
    else:
        # ── Sector Summary KPIs ───────────────────────────────────────────────
        sector_avgs = {}
        for sec, stocks in sector_data.items():
            avg_chg = np.mean([s["change"] for s in stocks])
            sector_avgs[sec] = round(avg_chg, 2)

        best_sec  = max(sector_avgs, key=sector_avgs.get)
        worst_sec = min(sector_avgs, key=sector_avgs.get)
        green_sec = sum(1 for v in sector_avgs.values() if v >= 0)
        red_sec   = sum(1 for v in sector_avgs.values() if v < 0)

        st.markdown(f"""<div class="krow">
          <div class="kpi up"><div class="klabel">Best Sector</div>
            <div class="kval" style="font-size:1rem">{best_sec}</div>
            <div class="ksub">▲ {sector_avgs[best_sec]:+.2f}% today</div></div>
          <div class="kpi dn"><div class="klabel">Worst Sector</div>
            <div class="kval" style="font-size:1rem">{worst_sec}</div>
            <div class="ksub">▼ {sector_avgs[worst_sec]:+.2f}% today</div></div>
          <div class="kpi up"><div class="klabel">Green Sectors</div>
            <div class="kval">{green_sec}</div>
            <div class="ksub">Sectors in green</div></div>
          <div class="kpi dn"><div class="klabel">Red Sectors</div>
            <div class="kval">{red_sec}</div>
            <div class="ksub">Sectors in red</div></div>
          <div class="kpi nu"><div class="klabel">Total Sectors</div>
            <div class="kval">{len(sector_avgs)}</div>
            <div class="ksub">Tracked today</div></div>
        </div>""", unsafe_allow_html=True)

        # ── Sector Bar Chart ──────────────────────────────────────────────────
        st.markdown('<div class="slabel">Sector Performance — Today</div>', unsafe_allow_html=True)

        sec_sorted = dict(sorted(sector_avgs.items(), key=lambda x: x[1], reverse=True))
        bar_colors = [GREEN if v >= 0 else RED for v in sec_sorted.values()]

        fig_sec = go.Figure(go.Bar(
            x=list(sec_sorted.keys()),
            y=list(sec_sorted.values()),
            marker_color=bar_colors,
            text=[f"{v:+.2f}%" for v in sec_sorted.values()],
            textposition="outside",
            textfont_color=TEXT,
        ))
        fig_sec.add_hline(y=0, line_color=BORDER, line_width=1)
        th(fig_sec, h=320, title="Sector Returns % — Today")
        fig_sec.update_yaxes(title_text="Change %")
        st.plotly_chart(fig_sec, use_container_width=True, config={"displayModeBar": False})

        # ── Treemap Heatmap ───────────────────────────────────────────────────
        st.markdown('<div class="slabel">Treemap — Market Overview</div>', unsafe_allow_html=True)

        tree_labels  = []
        tree_parents = []
        tree_values  = []
        tree_colors  = []
        tree_text    = []

        # Root
        tree_labels.append("Market")
        tree_parents.append("")
        tree_values.append(0)
        tree_colors.append(0)
        tree_text.append("Market")

        for sec, stocks in sector_data.items():
            sec_avg = sector_avgs.get(sec, 0)
            sec_val = sum(s["mktcap"] for s in stocks)
            tree_labels.append(sec)
            tree_parents.append("Market")
            tree_values.append(sec_val)
            tree_colors.append(sec_avg)
            tree_text.append(f"{sec}<br>{sec_avg:+.2f}%")

            for s in stocks:
                tree_labels.append(s["ticker"])
                tree_parents.append(sec)
                tree_values.append(max(s["mktcap"], 1e8))
                tree_colors.append(s["change"])
                tree_text.append(f"{s['ticker']}<br>{s['change']:+.2f}%<br>{s['price']}")

        fig_tree = go.Figure(go.Treemap(
            labels  = tree_labels,
            parents = tree_parents,
            values  = tree_values,
            text    = tree_text,
            customdata = tree_colors,
            marker  = dict(
                colors    = tree_colors,
                colorscale= [
                    [0.0,  "#cc1133"],
                    [0.35, "#882222"],
                    [0.5,  SURF2],
                    [0.65, "#224422"],
                    [1.0,  "#00aa44"],
                ],
                cmid      = 0,
                showscale = True,
                colorbar  = dict(
                    title = dict(text="Change %"),
                    tickfont = dict(color=TEXT),
                ),
            ),
            textinfo    = "text",
            hovertemplate = "<b>%{label}</b><br>Change: %{customdata:.2f}%<extra></extra>",
            pathbar     = dict(visible=True),
            tiling      = dict(packing="squarify"),
        ))

        fig_tree.update_layout(
            plot_bgcolor  = SURFACE,
            paper_bgcolor = BG,
            font          = dict(family="IBM Plex Mono", color=TEXT, size=11),
            title_font    = dict(color=HEAD, size=13, family="Syne"),
            margin        = dict(l=8, r=8, t=36, b=8),
            height        = 550,
            title         = f"{'NSE' if 'India' in market_sel else 'US'} Market Treemap — Size = Market Cap · Color = % Change",
        )
        st.plotly_chart(fig_tree, use_container_width=True, config={"displayModeBar": False})

        # ── Stock-level heatmap ───────────────────────────────────────────────
        st.markdown('<div class="slabel">Stock-wise Performance by Sector</div>', unsafe_allow_html=True)

        selected_sector = st.selectbox(
            "Select Sector",
            options=list(sector_data.keys()),
            label_visibility="collapsed"
        )

        if selected_sector in sector_data:
            stocks_in_sec = sector_data[selected_sector]
            stocks_sorted = sorted(stocks_in_sec, key=lambda x: x["change"], reverse=True)

            fig_stocks = go.Figure(go.Bar(
                x=[s["ticker"] for s in stocks_sorted],
                y=[s["change"] for s in stocks_sorted],
                marker_color=[GREEN if s["change"] >= 0 else RED for s in stocks_sorted],
                text=[f"{s['change']:+.2f}%" for s in stocks_sorted],
                textposition="outside",
                textfont_color=TEXT,
                customdata=[[s["price"]] for s in stocks_sorted],
                hovertemplate="<b>%{x}</b><br>Change: %{y:.2f}%<br>Price: %{customdata[0]:.2f}<extra></extra>",
            ))
            fig_stocks.add_hline(y=0, line_color=BORDER, line_width=1)
            th(fig_stocks, h=300, title=f"{selected_sector} Sector — Stock Performance")
            st.plotly_chart(fig_stocks, use_container_width=True, config={"displayModeBar": False})

            # Table
            df_sec = pd.DataFrame(stocks_sorted)[["ticker","price","change"]]
            df_sec.columns = ["Stock","Price","Change %"]
            df_sec["Change %"] = df_sec["Change %"].apply(lambda x: f"{x:+.2f}%")
            st.dataframe(df_sec, use_container_width=True, hide_index=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 12 — EARNINGS CALENDAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T12:
    st.markdown('<div class="slabel">📅 Earnings Calendar & Analysis</div>', unsafe_allow_html=True)

    # ── Fetch earnings data ───────────────────────────────────────────────────
    @st.cache_data(ttl=3600)
    def fetch_earnings(tkr):
        try:
            t = yf.Ticker(tkr)
            # Earnings history
            hist = t.earnings_history if hasattr(t, 'earnings_history') else None
            # Upcoming earnings date
            cal  = t.calendar if hasattr(t, 'calendar') else None
            # Quarterly earnings
            qtr  = t.quarterly_income_stmt if hasattr(t, 'quarterly_income_stmt') else None
            return hist, cal, qtr
        except: return None, None, None

    with st.spinner("Fetching earnings data..."):
        earn_hist, earn_cal, qtr_stmt = fetch_earnings(ticker)

    # ── Upcoming Earnings ─────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Upcoming Earnings Date</div>', unsafe_allow_html=True)

    next_earn_date = None
    if earn_cal is not None:
        try:
            if isinstance(earn_cal, dict):
                next_earn_date = earn_cal.get("Earnings Date", [None])[0]
            elif isinstance(earn_cal, pd.DataFrame) and "Earnings Date" in earn_cal.index:
                next_earn_date = earn_cal.loc["Earnings Date"].iloc[0]
        except: pass

    if next_earn_date:
        try:
            ned  = pd.Timestamp(next_earn_date)
            days = (ned - pd.Timestamp.now()).days
            col  = "up" if days > 30 else "wa" if days > 7 else "dn"
            st.markdown(f"""<div class="krow">
              <div class="kpi {col}"><div class="klabel">Next Earnings</div>
                <div class="kval" style="font-size:1rem">{ned.strftime('%d %b %Y')}</div>
                <div class="ksub">{"In " + str(days) + " days" if days >= 0 else "Already passed"}</div></div>
              <div class="kpi wa"><div class="klabel">Days Remaining</div>
                <div class="kval">{max(days,0)}</div>
                <div class="ksub">Trading days approx</div></div>
              <div class="kpi nu"><div class="klabel">Stock</div>
                <div class="kval" style="font-size:1rem">{ticker}</div>
                <div class="ksub">Current: {cur:.2f}</div></div>
            </div>""", unsafe_allow_html=True)
        except:
            st.info("Earnings date format could not be parsed.")
    else:
        st.info(f"Upcoming earnings date not available for `{ticker}`. Try US stocks like AAPL, MSFT.")

    # ── Earnings History ──────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Earnings History — EPS Estimate vs Actual</div>', unsafe_allow_html=True)

    if earn_hist is not None and not earn_hist.empty:
        try:
            eh = earn_hist.copy()
            eh = eh.reset_index()

            # Rename columns if needed
            col_map = {}
            for c in eh.columns:
                cl = c.lower()
                if "date" in cl:            col_map[c] = "Date"
                elif "actual" in cl:        col_map[c] = "EPS Actual"
                elif "estimate" in cl:      col_map[c] = "EPS Estimate"
                elif "surprise" in cl and "percent" in cl: col_map[c] = "Surprise %"
                elif "surprise" in cl:      col_map[c] = "Surprise"
            eh = eh.rename(columns=col_map)

            if "EPS Actual" in eh.columns and "EPS Estimate" in eh.columns:
                eh = eh.dropna(subset=["EPS Actual","EPS Estimate"])
                eh["Beat"] = eh["EPS Actual"] >= eh["EPS Estimate"]
                eh["Surprise $"] = (eh["EPS Actual"] - eh["EPS Estimate"]).round(3)

                # KPIs
                beat_count = eh["Beat"].sum()
                miss_count = len(eh) - beat_count
                beat_rate  = beat_count / len(eh) * 100 if len(eh) > 0 else 0
                avg_surp   = eh["Surprise $"].mean()

                st.markdown(f"""<div class="krow">
                  <div class="kpi up"><div class="klabel">Earnings Beats</div>
                    <div class="kval">{beat_count}</div>
                    <div class="ksub">Beat estimate</div></div>
                  <div class="kpi dn"><div class="klabel">Earnings Misses</div>
                    <div class="kval">{miss_count}</div>
                    <div class="ksub">Missed estimate</div></div>
                  <div class="kpi {'up' if beat_rate>=60 else 'wa' if beat_rate>=50 else 'dn'}">
                    <div class="klabel">Beat Rate</div>
                    <div class="kval">{beat_rate:.1f}%</div>
                    <div class="ksub">Historical accuracy</div></div>
                  <div class="kpi {'up' if avg_surp>=0 else 'dn'}"><div class="klabel">Avg Surprise</div>
                    <div class="kval">{avg_surp:+.3f}</div>
                    <div class="ksub">Avg EPS beat/miss</div></div>
                </div>""", unsafe_allow_html=True)

                # EPS Chart
                fig_eps = go.Figure()

                # EPS Estimate bars
                fig_eps.add_trace(go.Bar(
                    x=eh["Date"].astype(str) if "Date" in eh.columns else eh.index.astype(str),
                    y=eh["EPS Estimate"],
                    name="EPS Estimate",
                    marker_color=MUTED, opacity=0.6,
                ))

                # EPS Actual bars
                actual_colors = [GREEN if b else RED for b in eh["Beat"]]
                fig_eps.add_trace(go.Bar(
                    x=eh["Date"].astype(str) if "Date" in eh.columns else eh.index.astype(str),
                    y=eh["EPS Actual"],
                    name="EPS Actual",
                    marker_color=actual_colors, opacity=0.85,
                ))

                fig_eps.update_layout(
                    barmode="group",
                    plot_bgcolor=SURFACE, paper_bgcolor=BG,
                    font=dict(family="IBM Plex Mono", color=TEXT, size=11),
                    title_font=dict(color=HEAD, size=13, family="Syne"),
                    margin=dict(l=8, r=8, t=36, b=8),
                    legend=dict(bgcolor=SURF2, bordercolor=BORDER, borderwidth=1,
                                font_size=10, font_color=TEXT),
                    xaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED),
                    yaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED,
                               title="EPS ($)"),
                    height=350,
                    title="EPS — Estimate vs Actual (🟢 Beat · 🔴 Miss)",
                )
                st.plotly_chart(fig_eps, use_container_width=True, config={"displayModeBar": False})

                # Surprise chart
                surp_colors = [GREEN if v >= 0 else RED for v in eh["Surprise $"]]
                fig_surp = go.Figure(go.Bar(
                    x=eh["Date"].astype(str) if "Date" in eh.columns else eh.index.astype(str),
                    y=eh["Surprise $"],
                    marker_color=surp_colors,
                    text=[f"{v:+.3f}" for v in eh["Surprise $"]],
                    textposition="outside",
                    textfont_color=TEXT,
                    name="EPS Surprise",
                ))
                fig_surp.add_hline(y=0, line_color=BORDER, line_width=1)
                fig_surp.update_layout(
                    plot_bgcolor=SURFACE, paper_bgcolor=BG,
                    font=dict(family="IBM Plex Mono", color=TEXT, size=11),
                    title_font=dict(color=HEAD, size=13, family="Syne"),
                    margin=dict(l=8, r=8, t=36, b=8),
                    xaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED),
                    yaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED,
                               title="Surprise ($)"),
                    height=250,
                    title="EPS Surprise — How much did company beat/miss?",
                )
                st.plotly_chart(fig_surp, use_container_width=True, config={"displayModeBar": False})

                # Table
                st.markdown('<div class="slabel">Earnings History Table</div>', unsafe_allow_html=True)
                display_cols = [c for c in ["Date","EPS Estimate","EPS Actual","Surprise $","Beat"] if c in eh.columns]
                eh_display = eh[display_cols].copy()
                if "Date" in eh_display.columns:
                    eh_display["Date"] = eh_display["Date"].astype(str)
                if "Beat" in eh_display.columns:
                    eh_display["Beat"] = eh_display["Beat"].map({True: "✅ Beat", False: "❌ Miss"})
                st.dataframe(eh_display, use_container_width=True, hide_index=True)

            else:
                st.info("EPS data columns not found for this ticker.")
        except Exception as e:
            st.info(f"Could not parse earnings history. Try US stocks like AAPL, MSFT.")
    else:
        st.info("Earnings history not available. Try: `AAPL`, `MSFT`, `GOOGL`, `TSLA`")

    # ── Post-Earnings Stock Reaction ──────────────────────────────────────────
    st.markdown('<div class="slabel">Post-Earnings Stock Reaction</div>', unsafe_allow_html=True)

    if earn_hist is not None and not earn_hist.empty:
        try:
            eh2 = earn_hist.reset_index()
            reactions = []

            for _, row in eh2.iterrows():
                try:
                    earn_date = pd.Timestamp(row.get("Earnings Date", row.get("Date", None)))
                    if pd.isna(earn_date): continue

                    # Price before and after earnings
                    start = (earn_date - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
                    end   = (earn_date + pd.Timedelta(days=5)).strftime("%Y-%m-%d")
                    hist_data = yf.Ticker(ticker).history(start=start, end=end)

                    if len(hist_data) >= 2:
                        pre_price  = hist_data["Close"].iloc[0]
                        post_price = hist_data["Close"].iloc[-1]
                        reaction   = (post_price - pre_price) / pre_price * 100
                        reactions.append({
                            "Date":     earn_date.strftime("%b %Y"),
                            "Pre Price":  round(pre_price, 2),
                            "Post Price": round(post_price, 2),
                            "Reaction %": round(reaction, 2),
                        })
                except: continue

            if reactions:
                react_df = pd.DataFrame(reactions)
                react_colors = [GREEN if v >= 0 else RED for v in react_df["Reaction %"]]

                fig_react = go.Figure(go.Bar(
                    x=react_df["Date"],
                    y=react_df["Reaction %"],
                    marker_color=react_colors,
                    text=[f"{v:+.1f}%" for v in react_df["Reaction %"]],
                    textposition="outside",
                    textfont_color=TEXT,
                ))
                fig_react.add_hline(y=0, line_color=BORDER, line_width=1)
                fig_react.update_layout(
                    plot_bgcolor=SURFACE, paper_bgcolor=BG,
                    font=dict(family="IBM Plex Mono", color=TEXT, size=11),
                    title_font=dict(color=HEAD, size=13, family="Syne"),
                    margin=dict(l=8, r=8, t=36, b=8),
                    xaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED),
                    yaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED,
                               title="Price Change %"),
                    height=280,
                    title="Stock Price Reaction after Earnings (5-day window)",
                )
                st.plotly_chart(fig_react, use_container_width=True, config={"displayModeBar": False})
                st.dataframe(react_df, use_container_width=True, hide_index=True)
            else:
                st.info("Could not calculate post-earnings reactions.")
        except:
            st.info("Post-earnings reaction data not available.")

    # ── Quarterly Revenue & Income ─────────────────────────────────────────────
    st.markdown('<div class="slabel">Quarterly Revenue & Net Income</div>', unsafe_allow_html=True)

    if qtr_stmt is not None and not qtr_stmt.empty:
        try:
            rev_row = None
            inc_row = None
            for idx in qtr_stmt.index:
                idx_l = str(idx).lower()
                if "total revenue" in idx_l or "revenue" in idx_l:
                    rev_row = qtr_stmt.loc[idx]
                if "net income" in idx_l:
                    inc_row = qtr_stmt.loc[idx]

            if rev_row is not None or inc_row is not None:
                dates = [str(c)[:10] for c in qtr_stmt.columns]

                fig_qtr = go.Figure()
                if rev_row is not None:
                    fig_qtr.add_trace(go.Bar(
                        x=dates, y=rev_row.values / 1e9,
                        name="Revenue (B)", marker_color=ACCENT, opacity=0.8,
                    ))
                if inc_row is not None:
                    ni_colors = [GREEN if v >= 0 else RED for v in inc_row.values]
                    fig_qtr.add_trace(go.Bar(
                        x=dates, y=inc_row.values / 1e9,
                        name="Net Income (B)", marker_color=ni_colors, opacity=0.8,
                    ))

                fig_qtr.update_layout(
                    barmode="group",
                    plot_bgcolor=SURFACE, paper_bgcolor=BG,
                    font=dict(family="IBM Plex Mono", color=TEXT, size=11),
                    title_font=dict(color=HEAD, size=13, family="Syne"),
                    margin=dict(l=8, r=8, t=36, b=8),
                    legend=dict(bgcolor=SURF2, bordercolor=BORDER, borderwidth=1,
                                font_size=10, font_color=TEXT),
                    xaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED),
                    yaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=MUTED,
                               title="Billions ($)"),
                    height=320,
                    title="Quarterly Revenue & Net Income (in Billions)",
                )
                st.plotly_chart(fig_qtr, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Revenue/income rows not found in quarterly data.")
        except:
            st.info("Quarterly financials not available for this ticker.")
    else:
        st.info("Quarterly financial statements not available. Try US stocks.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 13 — CRYPTO & FOREX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T13:
    st.markdown('<div class="slabel">💹 Crypto & Forex Live Tracker</div>', unsafe_allow_html=True)

    CRYPTO_LIST = {
        "Bitcoin":  "BTC-USD", "Ethereum":  "ETH-USD",
        "Solana":   "SOL-USD", "BNB":       "BNB-USD",
        "XRP":      "XRP-USD", "Cardano":   "ADA-USD",
        "Dogecoin": "DOGE-USD","Avalanche": "AVAX-USD",
    }
    FOREX_LIST = {
        "USD/INR":  "USDINR=X", "EUR/INR":  "EURINR=X",
        "GBP/INR":  "GBPINR=X", "JPY/INR":  "JPYINR=X",
        "EUR/USD":  "EURUSD=X", "GBP/USD":  "GBPUSD=X",
        "USD/JPY":  "USDJPY=X", "AUD/USD":  "AUDUSD=X",
    }

    @st.cache_data(ttl=60)
    def fetch_live_prices(symbols_dict):
        results = []
        for name, sym in symbols_dict.items():
            try:
                d = yf.Ticker(sym).history(period="5d")
                if len(d) >= 2:
                    c = d["Close"].iloc[-1]
                    p = d["Close"].iloc[-2]
                    chg    = (c - p) / p * 100
                    hi     = d["High"].max()
                    lo     = d["Low"].min()
                    vol    = d["Volume"].iloc[-1] if "Volume" in d.columns else 0
                    results.append({
                        "Name": name, "Symbol": sym,
                        "Price": round(c, 4),
                        "Change %": round(chg, 2),
                        "5D High": round(hi, 4),
                        "5D Low":  round(lo, 4),
                        "Volume":  vol,
                    })
            except: pass
        return results

    # ── Crypto Section ────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">🪙 Cryptocurrency Prices</div>', unsafe_allow_html=True)

    with st.spinner("Fetching crypto prices..."):
        crypto_data = fetch_live_prices(CRYPTO_LIST)

    if crypto_data:
        # KPI strip
        kpi_html = '<div class="krow">'
        for c in crypto_data[:4]:
            col_c = "up" if c["Change %"] >= 0 else "dn"
            ar    = "▲" if c["Change %"] >= 0 else "▼"
            kpi_html += f"""<div class="kpi {col_c}">
                <div class="klabel">{c['Name']}</div>
                <div class="kval" style="font-size:1.1rem">${c['Price']:,.2f}</div>
                <div class="ksub">{ar} {abs(c['Change %']):.2f}% today</div>
            </div>"""
        kpi_html += '</div>'
        st.markdown(kpi_html, unsafe_allow_html=True)

        kpi_html2 = '<div class="krow">'
        for c in crypto_data[4:]:
            col_c = "up" if c["Change %"] >= 0 else "dn"
            ar    = "▲" if c["Change %"] >= 0 else "▼"
            kpi_html2 += f"""<div class="kpi {col_c}">
                <div class="klabel">{c['Name']}</div>
                <div class="kval" style="font-size:1.1rem">${c['Price']:,.4f}</div>
                <div class="ksub">{ar} {abs(c['Change %']):.2f}% today</div>
            </div>"""
        kpi_html2 += '</div>'
        st.markdown(kpi_html2, unsafe_allow_html=True)

        # Crypto bar chart
        crypto_df  = pd.DataFrame(crypto_data)
        bar_colors = [GREEN if v >= 0 else RED for v in crypto_df["Change %"]]
        fig_crypto = go.Figure(go.Bar(
            x=crypto_df["Name"], y=crypto_df["Change %"],
            marker_color=bar_colors,
            text=[f"{v:+.2f}%" for v in crypto_df["Change %"]],
            textposition="outside", textfont_color=TEXT,
        ))
        fig_crypto.add_hline(y=0, line_color=BORDER, line_width=1)
        fig_crypto.update_layout(
            plot_bgcolor=SURFACE, paper_bgcolor=BG,
            font=dict(family="IBM Plex Mono", color=TEXT, size=11),
            title_font=dict(color=HEAD, size=13, family="Syne"),
            margin=dict(l=8, r=8, t=36, b=8),
            xaxis=dict(gridcolor=GRID, linecolor=BORDER),
            yaxis=dict(gridcolor=GRID, linecolor=BORDER, title="Change %"),
            height=280, title="Crypto Performance — Today",
        )
        st.plotly_chart(fig_crypto, use_container_width=True, config={"displayModeBar": False})

        # Crypto detail chart
        st.markdown('<div class="slabel">Crypto Price Chart</div>', unsafe_allow_html=True)
        sel_crypto = st.selectbox("Select Crypto", list(CRYPTO_LIST.keys()), label_visibility="collapsed")
        sel_period = st.select_slider("Period", ["1mo","3mo","6mo","1y","2y"], value="1y", key="crypto_period")

        @st.cache_data(ttl=300)
        def fetch_crypto_chart(sym, per):
            try:
                d = yf.Ticker(sym).history(period=per)
                d = d.reset_index()
                d["Date"] = pd.to_datetime(d["Date"]).dt.tz_localize(None)
                return d
            except: return None

        cd = fetch_crypto_chart(CRYPTO_LIST[sel_crypto], sel_period)
        if cd is not None and not cd.empty:
            cd["CumRet"] = (cd["Close"] / cd["Close"].iloc[0] - 1) * 100
            fig_cd = go.Figure()
            fig_cd.add_trace(go.Scatter(
                x=cd["Date"], y=cd["Close"],
                line=dict(color=AMBER, width=2),
                fill="tozeroy",
                fillcolor=f"{'rgba(255,170,0,.06)' if DARK else 'rgba(187,119,0,.05)'}",
                name=sel_crypto,
            ))
            fig_cd.update_layout(
                plot_bgcolor=SURFACE, paper_bgcolor=BG,
                font=dict(family="IBM Plex Mono", color=TEXT, size=11),
                title_font=dict(color=HEAD, size=13, family="Syne"),
                margin=dict(l=8, r=8, t=36, b=8),
                xaxis=dict(gridcolor=GRID, linecolor=BORDER),
                yaxis=dict(gridcolor=GRID, linecolor=BORDER, title="Price (USD)"),
                height=320, title=f"{sel_crypto} — {sel_period}",
            )
            st.plotly_chart(fig_cd, use_container_width=True, config={"displayModeBar": False})

    # ── Forex Section ─────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">💱 Forex — Live Exchange Rates</div>', unsafe_allow_html=True)

    with st.spinner("Fetching forex rates..."):
        forex_data = fetch_live_prices(FOREX_LIST)

    if forex_data:
        kpi_fx = '<div class="krow">'
        for f in forex_data:
            col_c = "up" if f["Change %"] >= 0 else "dn"
            ar    = "▲" if f["Change %"] >= 0 else "▼"
            kpi_fx += f"""<div class="kpi {col_c}">
                <div class="klabel">{f['Name']}</div>
                <div class="kval" style="font-size:1.1rem">{f['Price']:,.4f}</div>
                <div class="ksub">{ar} {abs(f['Change %']):.3f}%</div>
            </div>"""
        kpi_fx += '</div>'
        st.markdown(kpi_fx, unsafe_allow_html=True)

        forex_df   = pd.DataFrame(forex_data)
        fx_colors  = [GREEN if v >= 0 else RED for v in forex_df["Change %"]]
        fig_fx = go.Figure(go.Bar(
            x=forex_df["Name"], y=forex_df["Change %"],
            marker_color=fx_colors,
            text=[f"{v:+.3f}%" for v in forex_df["Change %"]],
            textposition="outside", textfont_color=TEXT,
        ))
        fig_fx.add_hline(y=0, line_color=BORDER, line_width=1)
        fig_fx.update_layout(
            plot_bgcolor=SURFACE, paper_bgcolor=BG,
            font=dict(family="IBM Plex Mono", color=TEXT, size=11),
            title_font=dict(color=HEAD, size=13, family="Syne"),
            margin=dict(l=8, r=8, t=36, b=8),
            xaxis=dict(gridcolor=GRID, linecolor=BORDER),
            yaxis=dict(gridcolor=GRID, linecolor=BORDER, title="Change %"),
            height=260, title="Forex — Today's Change %",
        )
        st.plotly_chart(fig_fx, use_container_width=True, config={"displayModeBar": False})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 14 — STOCK SCREENER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T14:
    st.markdown('<div class="slabel">🔍 Stock Screener</div>', unsafe_allow_html=True)
    st.caption("Filter stocks based on technical & fundamental criteria")

    SCREEN_STOCKS = {
        "🇮🇳 NSE Large Cap": [
            "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","WIPRO.NS",
            "TATAMOTORS.NS","ADANIENT.NS","BAJFINANCE.NS","SUNPHARMA.NS",
            "MARUTI.NS","HCLTECH.NS","ICICIBANK.NS","SBIN.NS","NTPC.NS",
            "ONGC.NS","COALINDIA.NS","LTIM.NS","TECHM.NS","AXISBANK.NS",
            "KOTAKBANK.NS","TITAN.NS","ASIANPAINT.NS","NESTLEIND.NS","ITC.NS",
        ],
        "🇺🇸 US Large Cap": [
            "AAPL","MSFT","GOOGL","AMZN","NVDA","TSLA","META","NFLX",
            "JPM","BAC","V","MA","JNJ","UNH","XOM","CVX","HD","WMT",
            "DIS","PYPL","INTC","AMD","QCOM","ORCL","CRM",
        ],
    }

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Set Filters</div>', unsafe_allow_html=True)

    screen_market = st.radio("Stock Universe", list(SCREEN_STOCKS.keys()), horizontal=True)
    fc1, fc2, fc3 = st.columns(3)

    with fc1:
        rsi_min, rsi_max = st.slider("RSI Range", 0, 100, (0, 100), step=5)
        chg_min, chg_max = st.slider("Day Change % Range", -15.0, 15.0, (-15.0, 15.0), step=0.5)

    with fc2:
        ma_filter = st.selectbox("MA Filter", [
            "None",
            "Price > MA20 (Uptrend)",
            "Price < MA20 (Downtrend)",
            "MA20 > MA50 (Golden Cross)",
            "MA20 < MA50 (Death Cross)",
        ])
        vol_filter = st.selectbox("Volume Filter", [
            "None",
            "Volume Spike (>2x avg)",
            "High Volume (>1.5x avg)",
        ])

    with fc3:
        sort_by = st.selectbox("Sort By", ["Change %", "RSI", "Volume", "Price"])
        sort_asc = st.radio("Order", ["Descending", "Ascending"], horizontal=True)
        max_results = st.slider("Max Results", 5, 25, 10)

    run_screen = st.button("🔍 Run Screener", type="primary", use_container_width=True)

    if run_screen:
        tickers_to_screen = SCREEN_STOCKS[screen_market]
        screen_results = []

        prog = st.progress(0, text="Screening stocks...")
        for idx, tk in enumerate(tickers_to_screen):
            try:
                d = yf.Ticker(tk).history(period="3mo")
                if len(d) < 50:
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue

                c    = d["Close"].iloc[-1]
                p    = d["Close"].iloc[-2]
                chg  = (c - p) / p * 100
                vol  = d["Volume"].iloc[-1]
                avgv = d["Volume"].rolling(20).mean().iloc[-1]

                # RSI
                delta = d["Close"].diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rs    = gain / loss.replace(0, np.nan)
                rsi_v = (100 - 100/(1+rs)).iloc[-1]

                # MAs
                ma20 = d["Close"].rolling(20).mean().iloc[-1]
                ma50 = d["Close"].rolling(50).mean().iloc[-1]

                # Apply filters
                if not (rsi_min <= rsi_v <= rsi_max): 
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue
                if not (chg_min <= chg <= chg_max):
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue
                if ma_filter == "Price > MA20 (Uptrend)" and c <= ma20:
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue
                if ma_filter == "Price < MA20 (Downtrend)" and c >= ma20:
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue
                if ma_filter == "MA20 > MA50 (Golden Cross)" and ma20 <= ma50:
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue
                if ma_filter == "MA20 < MA50 (Death Cross)" and ma20 >= ma50:
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue
                if vol_filter == "Volume Spike (>2x avg)" and vol <= avgv * 2:
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue
                if vol_filter == "High Volume (>1.5x avg)" and vol <= avgv * 1.5:
                    prog.progress((idx+1)/len(tickers_to_screen))
                    continue

                screen_results.append({
                    "Ticker":    tk.replace(".NS",""),
                    "Price":     round(c, 2),
                    "Change %":  round(chg, 2),
                    "RSI":       round(rsi_v, 1),
                    "MA20":      round(ma20, 2),
                    "MA50":      round(ma50, 2),
                    "Volume":    f"{vol/1e6:.1f}M",
                    "vs MA20":   f"{((c-ma20)/ma20*100):+.1f}%",
                    "Signal":    "🟢 Bull" if c > ma20 and rsi_v < 65 else "🔴 Bear" if c < ma20 and rsi_v > 35 else "⚪ Neutral",
                })
            except: pass
            prog.progress((idx+1)/len(tickers_to_screen))

        prog.empty()

        if screen_results:
            res_df = pd.DataFrame(screen_results)
            sort_col = {"Change %":"Change %","RSI":"RSI","Volume":"Volume","Price":"Price"}.get(sort_by,"Change %")
            if sort_col in res_df.columns:
                try:
                    res_df[sort_col] = pd.to_numeric(res_df[sort_col].astype(str).str.replace("%","").str.replace("M",""), errors="coerce")
                    res_df = res_df.sort_values(sort_col, ascending=(sort_asc=="Ascending"))
                except: pass

            res_df = res_df.head(max_results)

            st.markdown(f"""<div class="krow">
              <div class="kpi nu"><div class="klabel">Stocks Screened</div>
                <div class="kval">{len(tickers_to_screen)}</div></div>
              <div class="kpi up"><div class="klabel">Passed Filters</div>
                <div class="kval">{len(res_df)}</div></div>
              <div class="kpi up"><div class="klabel">Bullish</div>
                <div class="kval">{(res_df['Signal'].str.contains('Bull')).sum()}</div></div>
              <div class="kpi dn"><div class="klabel">Bearish</div>
                <div class="kval">{(res_df['Signal'].str.contains('Bear')).sum()}</div></div>
            </div>""", unsafe_allow_html=True)

            # Chart
            bar_c = [GREEN if v else RED for v in res_df["Change %"] >= 0] if "Change %" in res_df.columns else [ACCENT]*len(res_df)
            fig_sc = go.Figure(go.Bar(
                x=res_df["Ticker"], y=res_df["Change %"],
                marker_color=bar_c,
                text=[f"{v:+.2f}%" for v in res_df["Change %"]],
                textposition="outside", textfont_color=TEXT,
            ))
            fig_sc.add_hline(y=0, line_color=BORDER, line_width=1)
            fig_sc.update_layout(
                plot_bgcolor=SURFACE, paper_bgcolor=BG,
                font=dict(family="IBM Plex Mono", color=TEXT, size=11),
                title_font=dict(color=HEAD, size=13, family="Syne"),
                margin=dict(l=8, r=8, t=36, b=8),
                xaxis=dict(gridcolor=GRID, linecolor=BORDER),
                yaxis=dict(gridcolor=GRID, linecolor=BORDER, title="Change %"),
                height=300, title="Screener Results — Change %",
            )
            st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})
            st.dataframe(res_df, use_container_width=True, hide_index=True)

            # Export
            csv = res_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export Results CSV", csv,
                               f"screener_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                               "text/csv")
        else:
            st.warning("No stocks matched your filters. Try relaxing the criteria.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 15 — PRICE ALERTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with T15:
    st.markdown('<div class="slabel">🔔 Price Alert System</div>', unsafe_allow_html=True)
    st.caption("Set alerts for price levels, RSI, and technical conditions. Alerts are checked in this session.")

    # Session state for alerts
    if "alerts" not in st.session_state:
        st.session_state.alerts = []
    if "triggered_alerts" not in st.session_state:
        st.session_state.triggered_alerts = []

    # ── Add Alert ─────────────────────────────────────────────────────────────
    st.markdown('<div class="slabel">Add New Alert</div>', unsafe_allow_html=True)

    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        alert_ticker = st.text_input("Ticker", value=ticker, key="alert_tk").upper().strip()
    with ac2:
        alert_type = st.selectbox("Alert Type", [
            "Price Above", "Price Below",
            "RSI Above 70 (Overbought)", "RSI Below 30 (Oversold)",
            "Price crosses MA20", "Volume Spike (2x)",
        ])
    with ac3:
        alert_value = st.number_input(
            "Target Value",
            value=float(round(cur * 1.05, 2)),
            min_value=0.0, step=1.0,
            disabled=("RSI" in alert_type or "MA" in alert_type or "Volume" in alert_type),
        )
    with ac4:
        alert_note = st.text_input("Note (optional)", placeholder="e.g. Buy signal")

    if st.button("➕ Add Alert", type="primary"):
        new_alert = {
            "id":       len(st.session_state.alerts) + 1,
            "ticker":   alert_ticker,
            "type":     alert_type,
            "value":    alert_value,
            "note":     alert_note,
            "status":   "🟡 Active",
            "created":  datetime.datetime.now().strftime("%H:%M:%S"),
        }
        st.session_state.alerts.append(new_alert)
        st.success(f"✅ Alert added for {alert_ticker} — {alert_type}")

    # ── Check Alerts ──────────────────────────────────────────────────────────
    if st.session_state.alerts:
        if st.button("🔄 Check All Alerts Now"):
            triggered = []
            for alert in st.session_state.alerts:
                if alert["status"] == "✅ Triggered": continue
                try:
                    d = yf.Ticker(alert["ticker"]).history(period="5d")
                    if d.empty: continue
                    c    = d["Close"].iloc[-1]
                    p    = d["Close"].iloc[-2]
                    vol  = d["Volume"].iloc[-1]
                    avgv = d["Volume"].rolling(5).mean().iloc[-1]

                    # RSI
                    delta = d["Close"].diff()
                    gain  = delta.clip(lower=0).rolling(14).mean()
                    loss  = (-delta.clip(upper=0)).rolling(14).mean()
                    rs    = gain / loss.replace(0, np.nan)
                    rsi_a = (100 - 100/(1+rs)).iloc[-1]

                    # MA20
                    ma20a = d["Close"].rolling(20).mean().iloc[-1]
                    ma20p = d["Close"].rolling(20).mean().iloc[-2]

                    fired = False
                    if alert["type"] == "Price Above"      and c >= alert["value"]: fired = True
                    elif alert["type"] == "Price Below"    and c <= alert["value"]: fired = True
                    elif "RSI Above 70" in alert["type"]   and rsi_a >= 70:         fired = True
                    elif "RSI Below 30" in alert["type"]   and rsi_a <= 30:         fired = True
                    elif "MA20" in alert["type"]           and p < ma20p and c >= ma20a: fired = True
                    elif "Volume Spike" in alert["type"]   and vol >= avgv * 2:     fired = True

                    if fired:
                        alert["status"] = "✅ Triggered"
                        alert["triggered_at"] = datetime.datetime.now().strftime("%H:%M:%S")
                        alert["current_price"] = round(c, 2)
                        triggered.append(alert)
                except: pass

            if triggered:
                st.balloons()
                for t_alert in triggered:
                    st.error(f"🔔 ALERT TRIGGERED! {t_alert['ticker']} — {t_alert['type']} @ {t_alert.get('current_price','N/A')} | Note: {t_alert['note']}")
            else:
                st.info("No alerts triggered yet. Prices haven't hit your targets.")

        # ── Active Alerts ─────────────────────────────────────────────────────
        st.markdown('<div class="slabel">Your Alerts</div>', unsafe_allow_html=True)

        for i, alert in enumerate(st.session_state.alerts):
            cls = "bl" if alert["status"] == "✅ Triggered" else "bn"
            st.markdown(f"""<div class="sig {cls}">
                <strong>{alert['status']} · {alert['ticker']} · {alert['type']}</strong>
                {"· Target: " + str(alert['value']) if alert['value'] else ""}
                {"· " + alert['note'] if alert['note'] else ""}
                · Added: {alert['created']}
                {"· Triggered at: " + alert.get('triggered_at','') + " @ " + str(alert.get('current_price','')) if alert['status']=='✅ Triggered' else ""}
            </div>""", unsafe_allow_html=True)

        # Clear button
        col_x1, col_x2 = st.columns(2)
        with col_x1:
            if st.button("🗑️ Clear All Alerts"):
                st.session_state.alerts = []
                st.rerun()
        with col_x2:
            if st.button("🗑️ Clear Triggered Only"):
                st.session_state.alerts = [a for a in st.session_state.alerts if a["status"] != "✅ Triggered"]
                st.rerun()

        # ── Alert Stats ───────────────────────────────────────────────────────
        total_al  = len(st.session_state.alerts)
        active_al = sum(1 for a in st.session_state.alerts if a["status"] == "🟡 Active")
        trig_al   = sum(1 for a in st.session_state.alerts if a["status"] == "✅ Triggered")

        st.markdown(f"""<div class="krow">
          <div class="kpi nu"><div class="klabel">Total Alerts</div><div class="kval">{total_al}</div></div>
          <div class="kpi wa"><div class="klabel">Active</div><div class="kval">{active_al}</div></div>
          <div class="kpi up"><div class="klabel">Triggered</div><div class="kval">{trig_al}</div></div>
        </div>""", unsafe_allow_html=True)

    else:
        st.info("No alerts set yet. Add your first alert above! 👆")

    # ── Quick Alert Templates ─────────────────────────────────────────────────
    st.markdown('<div class="slabel">Quick Alert Templates</div>', unsafe_allow_html=True)
    templates = [
        ("RSI Oversold", f"Set RSI < 30 alert on {ticker} — potential buy signal"),
        ("5% Breakout",  f"Set price above {round(cur*1.05,2)} alert on {ticker}"),
        ("5% Stop Loss", f"Set price below {round(cur*0.95,2)} alert on {ticker}"),
        ("Volume Spike", f"Set volume spike alert on {ticker} — unusual activity"),
    ]
    t1c, t2c = st.columns(2)
    for i, (title, desc) in enumerate(templates):
        with (t1c if i % 2 == 0 else t2c):
            st.markdown(f'<div class="sig bn"><strong>💡 {title}</strong><br>{desc}</div>',
                        unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div style='margin-top:28px;border-top:1px solid {BORDER};padding-top:10px;
font-family:IBM Plex Mono;font-size:.55rem;color:{MUTED};letter-spacing:.1em'>
MARKETLENS · DATA VIA YAHOO FINANCE · EDUCATIONAL USE ONLY · @PRASHANT MUKUNDRAO MESHRAM
</div>""", unsafe_allow_html=True)