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
    st.session_state.theme = "light"   # default = light (more readable)

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

# ── Tabs ──────────────────────────────────────────────────────────────────────
T1,T2,T3,T4,T5 = st.tabs(["📊  Price","📉  Indicators","🏢  Fundamentals","🔄  Compare","💼  Portfolio"])

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

# Footer
st.markdown(f"""
<div style='margin-top:28px;border-top:1px solid {BORDER};padding-top:10px;
font-family:IBM Plex Mono;font-size:.55rem;color:{MUTED};letter-spacing:.1em'>
MARKETLENS · DATA VIA YAHOO FINANCE · EDUCATIONAL USE ONLY · NOT FINANCIAL ADVICE
</div>""",unsafe_allow_html=True)