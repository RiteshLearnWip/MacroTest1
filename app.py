import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
from datetime import datetime

# --- SETTING A USER AGENT (The Secret Sauce) ---
# This prevents Yahoo from seeing the request as a 'bot'
import requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# --- Constants ---
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

# --- Optimized Data Fetching ---
@st.cache_data(ttl=1800) # 30-minute cache to reduce hits
def get_data_safely():
    try:
        # Fetching ALL data in ONE go (Batching)
        tickers_to_fetch = NIFTY_50_TICKERS + ["^NSEI", "INR=X", "BZ=F"]
        data = yf.download(tickers_to_fetch, period="2d", session=session, silent=True)
        
        # 1. Macro Metrics
        macro = {
            "Nifty 50": {"val": data['Close']['^NSEI'].iloc[-1], "chg": (data['Close']['^NSEI'].iloc[-1]/data['Close']['^NSEI'].iloc[-2]-1)*100},
            "USD/INR": {"val": data['Close']['INR=X'].iloc[-1], "chg": (data['Close']['INR=X'].iloc[-1]/data['Close']['INR=X'].iloc[-2]-1)*100},
            "Brent Crude": {"val": data['Close']['BZ=F'].iloc[-1], "chg": (data['Close']['BZ=F'].iloc[-1]/data['Close']['BZ=F'].iloc[-2]-1)*100}
        }
        
        # 2. Market Breadth
        advances = 0
        declines = 0
        for t in NIFTY_50_TICKERS:
            if data['Close'][t].iloc[-1] > data['Close'][t].iloc[-2]:
                advances += 1
            else:
                declines += 1
                
        return macro, advances, declines, None
    except Exception as e:
        return None, 0, 0, str(e)

# --- Layout ---
st.title("🛡️ Macro & Sentiment Dashboard")

# Fetch data
macro_metrics, adv, dec, error = get_data_safely()

if error:
    if "Rate limit" in error or "429" in error:
        st.warning("⚠️ Yahoo Finance is currently rate-limiting this server. Showing last cached data or try again in 5 minutes.")
    else:
        st.error(f"Error fetching data: {error}")

if macro_metrics:
    # Top Metrics Row
    cols = st.columns(3)
    for i, (name, d) in enumerate(macro_metrics.items()):
        cols[i].metric(name, f"{d['val']:,.2f}", f"{d['chg']:.2f}%")

    st.divider()

    # Breadth Row
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Market Breadth (A/D)")
        fig = go.Figure(go.Bar(x=[adv, dec], y=['Advances', 'Declines'], orientation='h', marker_color=['#2ecc71', '#e74c3c']))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"A/D Ratio: {adv/dec:.2f}" if dec > 0 else "N/A")

# RSS Feed (Always shows regardless of data error)
st.divider()
st.subheader("🗞️ High-Signal News")
try:
    feed = feedparser.parse("https://www.livemint.com/rss/markets")
    for entry in feed.entries[:3]:
        st.markdown(f"**{entry.title}**")
        st.caption(f"[Read Article]({entry.link})")
except:
    st.write("News feed temporarily unavailable.")
