import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
from datetime import datetime

# --- Constants & Configuration ---
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

# --- Data Fetching Logic ---
@st.cache_data(ttl=3600)
def get_market_breadth():
    """Calculates Advance/Decline ratio from Nifty 50 stocks."""
    advances, declines = 0, 0
    # Fetching only the last 2 days of data for the 50 tickers
    data = yf.download(NIFTY_50_TICKERS, period="2d", group_by='ticker', silent=True)
    
    for ticker in NIFTY_50_TICKERS:
        try:
            prev_close = data[ticker]['Close'].iloc[0]
            curr_close = data[ticker]['Close'].iloc[-1]
            if curr_close > prev_close:
                advances += 1
            elif curr_close < prev_close:
                declines += 1
        except:
            continue
    return advances, declines

@st.cache_data(ttl=3600)
def get_macro_metrics():
    tickers = {"Nifty 50": "^NSEI", "USD/INR": "INR=X", "Brent Crude": "BZ=F"}
    results = {}
    for label, sym in tickers.items():
        hist = yf.Ticker(sym).history(period="2d")
        results[label] = {"val": hist['Close'].iloc[-1], "chg": (hist['Close'].iloc[-1]/hist['Close'].iloc[-2]-1)*100}
    return results

# --- Dashboard Layout ---
st.title("🛡️ Macro & Sentiment Dashboard")

# Top Metrics Row
metrics = get_macro_metrics()
cols = st.columns(len(metrics))
for i, (name, d) in enumerate(metrics.items()):
    cols[i].metric(name, f"{d['val']:,.2f}", f"{d['chg']:.2f}%")

st.divider()

# Market Breadth & Sentiment Row
col_breadth, col_tech = st.columns([1, 1])

with col_breadth:
    st.subheader("Market Breadth (A/D Ratio)")
    adv, dec = get_market_breadth()
    fig_breadth = go.Figure(go.Bar(
        x=[adv, dec],
        y=['Advances', 'Declines'],
        orientation='h',
        marker_color=['#2ecc71', '#e74c3c']
    ))
    fig_breadth.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_breadth, use_container_width=True)
    st.caption(f"Ratio: {adv/dec:.2f} (Bulls leading)" if dec > 0 else "N/A")

with col_tech:
    st.subheader("Key Price Levels")
    # Fetching levels (Placeholder logic for Gaps/Swings)
    nifty_hist = yf.Ticker("^NSEI").history(period="30d")
    s_high, s_low = nifty_hist['High'].max(), nifty_hist['Low'].min()
    st.write(f"🚩 **30D Resistance:** {s_high:,.0f}")
    st.write(f"🟢 **30D Support:** {s_low:,.0f}")
    st.progress(int((nifty_hist['Close'].iloc[-1] - s_low) / (s_high - s_low) * 100), text="Position in Range")

# News & RSS Feed
st.divider()
st.subheader("🗞️ High-Signal News Feed")
feed = feedparser.parse("https://www.livemint.com/rss/markets")
for entry in feed.entries[:5]:
    with st.expander(f"{entry.title}"):
        st.write(entry.summary if 'summary' in entry else "Click link for details.")
        st.markdown(f"[Read full article]({entry.link})")
