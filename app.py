import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
from datetime import datetime
import requests

# --- Browser Simulation ---
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# --- Configuration ---
NIFTY_50_TICKERS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS",
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
    "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS",
    "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS",
    "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS",
    "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

st.set_page_config(page_title="Macro Pulse", layout="wide")

# --- Data Engine ---
@st.cache_data(ttl=1800)
def get_data_safely():
    try:
        tickers_to_fetch = NIFTY_50_TICKERS + ["^NSEI", "INR=X", "BZ=F"]
        # FIXED: Changed 'silent' to 'progress'
        data = yf.download(tickers_to_fetch, period="5d", session=session, progress=False)
        
        if data.empty:
            return None, 0, 0, "No data returned from Yahoo Finance."

        # Macro Metrics Logic
        macro = {
            "Nifty 50": {"val": data['Close']['^NSEI'].iloc[-1], "chg": (data['Close']['^NSEI'].iloc[-1]/data['Close']['^NSEI'].iloc[-2]-1)*100},
            "USD/INR": {"val": data['Close']['INR=X'].iloc[-1], "chg": (data['Close']['INR=X'].iloc[-1]/data['Close']['INR=X'].iloc[-2]-1)*100},
            "Brent Crude": {"val": data['Close']['BZ=F'].iloc[-1], "chg": (data['Close']['BZ=F'].iloc[-1]/data['Close']['BZ=F'].iloc[-2]-1)*100}
        }
        
        # Breadth Calculation
        advances = 0
        declines = 0
        for t in NIFTY_50_TICKERS:
            try:
                if data['Close'][t].iloc[-1] > data['Close'][t].iloc[-2]:
                    advances += 1
                else:
                    declines += 1
            except:
                continue
                
        return macro, advances, declines, None
    except Exception as e:
        return None, 0, 0, str(e)

# --- Dashboard View ---
st.title("🛡️ Macro & Sentiment Dashboard")

macro_metrics, adv, dec, error = get_data_safely()

if error:
    st.error(f"⚠️ Error: {error}")
    if "429" in error:
        st.info("Yahoo Finance is currently rate-limiting. This usually clears up in a few minutes.")

if macro_metrics:
    # 1. Metrics Header
    m_cols = st.columns(3)
    for i, (name, d) in enumerate(macro_metrics.items()):
        m_cols[i].metric(name, f"{d['val']:,.2f}", f"{d['chg']:.2f}%")

    st.divider()

    # 2. Market Breadth Visualization
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.subheader("Nifty 50 Breadth (A/D)")
        fig = go.Figure(go.Bar(
            x=[adv, dec], 
            y=['Advances', 'Declines'], 
            orientation='h', 
            marker_color=['#2ecc71', '#e74c3c']
        ))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("Market Commentary")
        ratio = adv/dec if dec > 0 else 0
        if ratio > 1.5:
            st.success(f"Bulls are in control with an A/D ratio of {ratio:.2f}.")
        elif ratio < 0.7:
            st.warning(f"Bears are dominating. A/D ratio is weak at {ratio:.2f}.")
        else:
            st.info(f"Market is in a sideways/neutral tug-of-war. Ratio: {ratio:.2f}")

# 3. News Feed
st.divider()
st.subheader("🗞️ High-Signal News")
try:
    feed = feedparser.parse("https://www.livemint.com/rss/markets")
    for entry in feed.entries[:5]:
        st.markdown(f"**{entry.title}**")
        st.caption(f"[Read Article]({entry.link})")
except:
    st.write("News feed is temporarily refreshing.")

with st.sidebar:
    st.write(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")
    if st.button("Force Refresh"):
        st.cache_data.clear()
        st.rerun()
