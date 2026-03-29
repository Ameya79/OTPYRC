"""
OTPYRC - Live Crypto Price Tracker
====================================
Uses the FREE CoinGecko API (no API key needed).

FIX FOR 429 (Rate Limit):
    - API responses are now CACHED for 60 seconds using @st.cache_data
    - This means Streamlit won't call CoinGecko again on every dropdown click/rerun
    - Only a manual "Refresh" or waiting 60s triggers a new API call
    - Added retry logic with exponential backoff as a safety net

HOW TO RUN:
    pip install streamlit requests pandas
    streamlit run app.py

REMINDERS:
    - CoinGecko free tier = ~10-30 calls/min. Cache TTL (60s) keeps you safe.
    - Coin IDs must be CoinGecko slugs: "bitcoin", "ethereum", NOT "BTC"
      -> Valid IDs: https://api.coingecko.com/api/v3/coins/list
    - Sparkline is always in USD on the free tier (CoinGecko limitation)
    - If you STILL get 429s, increase CACHE_TTL_SECONDS to 120 or 180
    - If you have a CoinGecko API key, add it as: headers={"x-cg-demo-api-key": "YOUR_KEY"}
"""

import time
import streamlit as st
import requests
import pandas as pd

# ─────────────────────────────────────────────
# CONFIG — tweak these if you keep hitting 429
# ─────────────────────────────────────────────
CACHE_TTL_SECONDS = 60   # How long to reuse cached data before calling API again
MAX_RETRIES = 3           # How many times to retry on 429 before giving up
RETRY_DELAY = 5           # Seconds to wait between retries

# ─────────────────────────────────────────────
# CACHED API FUNCTIONS
# @st.cache_data(ttl=60) means:
#   - First call -> hits the API, stores result
#   - Next calls within 60s -> returns stored result, NO new API call
#   - After 60s -> fetches fresh data again
# This is the main fix for 429 errors.
# ─────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Fetching live prices...")
def fetch_prices(coins: str, currencies: str):
    """Fetch current prices + 24hr change from CoinGecko /simple/price"""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coins,
        "vs_currencies": currencies,
        "include_24hr_change": "true",
        "include_last_updated_at": "true"
    }
    for attempt in range(MAX_RETRIES):
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json(), None
        elif resp.status_code == 429:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # wait 5s, 10s, 15s...
            else:
                return None, 429
        else:
            return None, resp.status_code
    return None, 429


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Fetching 7-day trends...")
def fetch_sparklines(coins: str):
    """Fetch 7-day sparkline price arrays from CoinGecko /coins/markets"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": coins,
        "sparkline": "true"
    }
    for attempt in range(MAX_RETRIES):
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            result = {}
            for coin_data in resp.json():
                result[coin_data["id"]] = coin_data["sparkline_in_7d"]["price"]
            return result, None
        elif resp.status_code == 429:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return {}, 429
        else:
            return {}, resp.status_code
    return {}, 429


# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────
st.title("OTPYRC")
st.markdown("OTPYRC fetches live crypto prices using the CoinGecko API.")

st.sidebar.header("🔧 Controls")
coins = st.sidebar.text_input(
    "Enter Coin IDs (comma separated):",
    value="bitcoin,ethereum,dogecoin"
)
currencies = st.sidebar.text_input(
    "Enter Currencies (comma separated):",
    value="usd,inr,eur"
)

st.sidebar.markdown("---")

# Refresh button: clears the cache so next run fetches fresh data
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()  # wipe cached responses so API is called again
    st.rerun()

st.sidebar.info(f"💡 Data auto-refreshes every {CACHE_TTL_SECONDS}s to avoid rate limits.")

# ─────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────
price_data, price_err = fetch_prices(coins, currencies)
sparkline_data, spark_err = fetch_sparklines(coins)

# Friendly error messages for each HTTP error code
ERROR_MESSAGES = {
    429: "⛔ Rate limited by CoinGecko (429). Wait ~60 seconds and click Refresh.",
    400: "❌ Bad request (400) — check your coin IDs are valid CoinGecko slugs.",
    500: "🔥 CoinGecko server error (500) — their end, not yours. Try again later.",
}

if price_err:
    msg = ERROR_MESSAGES.get(price_err, f"API Error {price_err} — try again later.")
    st.error(msg)
    st.stop()  # halt the rest of the script, nothing to show

# ─────────────────────────────────────────────
# PROCESS PRICES
# ─────────────────────────────────────────────
df = pd.DataFrame(price_data).T   # transpose: rows=coins, cols=price keys

price_cols_only = [
    col for col in df.columns
    if not col.endswith("_24h_change") and not col.endswith("last_updated_at")
]

st.write("### Current Prices Table")
st.dataframe(df[price_cols_only])

currency_list = [c.strip().lower() for c in currencies.split(",")]
selected_currency = st.selectbox("Select currency to visualize:", currency_list)

price_col = selected_currency
change_col = selected_currency + "_24h_change"

if change_col not in df.columns:
    df[change_col] = pd.NA

if price_col in df.columns:
    clean_df = df[[price_col, change_col]].copy()
    clean_df[price_col] = pd.to_numeric(clean_df[price_col], errors="coerce")
    clean_df[change_col] = pd.to_numeric(clean_df[change_col], errors="coerce")
    clean_df = clean_df.rename(columns={price_col: "Price", change_col: "24hr change"})

    for coin_name in clean_df.index:
        value = clean_df.loc[coin_name, "24hr change"]
        if pd.notna(value):
            rounded = round(float(value), 2)
            color = "green" if rounded >= 0 else "red"
            sign = "+" if rounded >= 0 else ""
            clean_df.loc[coin_name, "24hr change"] = (
                f"<span style='color:{color};font-weight:bold'>{sign}{rounded}%</span>"
            )
        else:
            clean_df.loc[coin_name, "24hr change"] = "N/A"

    st.write("### Change Metrics")
    clean_df = clean_df.reset_index().rename(columns={"index": "coin"})
    st.markdown(clean_df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.warning("Selected currency not found in data.")

# ─────────────────────────────────────────────
# SPARKLINE CHARTS
# ─────────────────────────────────────────────
st.write("### 📈 7-Day Price Trends (USD)")

if spark_err:
    st.warning(f"Sparkline data unavailable ({spark_err}) — showing prices only.")
else:
    coin_list = [c.strip().lower() for c in coins.split(",")]
    cols = st.columns(len(coin_list))
    for idx, coin in enumerate(coin_list):
        if coin in sparkline_data:
            with cols[idx]:
                st.markdown(f"**{coin.upper()}**")
                spark_df = pd.DataFrame(sparkline_data[coin], columns=["Price"])
                st.line_chart(spark_df, height=180, use_container_width=True)

# ─────────────────────────────────────────────
# BAR CHART
# ─────────────────────────────────────────────
if price_col in df.columns:
    st.write("### Current Price Comparison")
    bar_data = pd.to_numeric(df[price_col], errors="coerce")
    st.bar_chart(bar_data)
