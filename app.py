import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
from datetime import datetime

# --- Configuration & Ticker List ---
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

st.set_page_config(page_title="Macro Pulse Dashboard", layout="wide")

# --- Optimized Data Engine ---
@st.cache_data(ttl=1800)
def get_verified_data():
    try:
        # Fetching all in one batch as verified in Colab
        all_tickers = NIFTY_50_TICKERS + ["^NSEI", "INR=X", "BZ=F"]
        data = yf.download(all_tickers, period="5d", progress=False)
        
        if data.empty:
            return None, 0, 0, "Data fetch returned empty. Check Yahoo Finance status."

        # 1. Macro Metrics Extraction
        macro = {
            "Nifty 50": {"val": data['Close']['^NSEI'].iloc[-1], "chg": (data['Close']['^NSEI'].iloc[-1]/data['Close']['^NSEI'].iloc[-2]-1)*100},
            "USD/INR": {"val": data['Close']['INR=X'].iloc[-1], "chg": (data['Close']['INR=X'].iloc[-1]/data['Close']['INR=X'].iloc[-2]-1)*100},
            "Brent Crude": {"val": data['Close']['BZ=F'].iloc[-1], "chg": (data['Close']['BZ=F'].iloc[-1]/data['Close']['BZ=F'].iloc[-2]-1)*100}
        }
        
        # 2. Advance/Decline Logic
        advances = sum(1 for t in NIFTY_50_TICKERS if data['Close'][t].iloc[-1] > data['Close'][t].iloc[-2])
        declines = len(NIFTY_50_TICKERS) - advances
                
        return macro, advances, declines, None
    except Exception as e:
        return None, 0, 0, str(e)

# --- UI Construction ---
st.title("🛡️ Macro & Sentiment Dashboard")

macro_metrics, adv, dec, error = get_verified_data()

if error:
    st.error(f"❌ Error: {error}")
else:
    # Row 1: The Vital Signs
    m_cols = st.columns(3)
    for i, (name, d) in enumerate(macro_metrics.items()):
        m_cols[i].metric(name, f"{d['val']:,.2f}", f"{d['chg']:.2f}%")

    st.divider()

    # Row 2: Market Internal (Breadth)
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.subheader("Nifty 50 Breadth (A/D)")
        fig = go.Figure(go.Bar(
            x=[adv, dec], 
            y=['Advances', 'Declines'], 
            orientation='h', 
            marker_color=['#2ecc71', '#e74c3c']
        ))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_r:
        st.subheader("First-Principles Signal")
        ad_ratio = adv/dec if dec > 0 else 0
        st.metric("A/D Ratio", f"{ad_ratio:.2f}")
        if ad_ratio > 1.5:
            st.success("Strong breadth. The rally has broad participation.")
        elif ad_ratio < 0.7:
            st.warning("Weak breadth. Selling pressure is systemic.")
        else:
            st.info("Neutral breadth. Market is seeking direction.")

# Row 3: High-Signal News
st.divider()
st.subheader("🗞️ Macro & Fintech Narrative")
try:
    feed = feedparser.parse("https://www.livemint.com/rss/markets")
    for entry in feed.entries[:5]:
        st.markdown(f"**{entry.title}** ([Link]({entry.link}))")
except:
    st.write("News feed refreshing...")

with st.sidebar:
    st.write(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")
    if st.button("Force Refresh"):
        st.cache_data.clear()
        st.rerun()
