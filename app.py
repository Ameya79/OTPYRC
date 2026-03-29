"""
REMINDERS:
    - Demo key limit: 30 calls/min — the 60s cache keeps you well under this
    - Coin IDs are CoinGecko slugs: "bitcoin", "ethereum", NOT "BTC"
      -> Find valid IDs: https://api.coingecko.com/api/v3/coins/list
    - Sparklines are always USD (CoinGecko free tier limitation)
    - If cache needs clearing, click Refresh in sidebar
"""

import time
import streamlit as st
import requests
import pandas as pd

#optional hardcode
API_KEY = ""   # e.g. "CG-abc123..." — leave "" to use sidebar input instead


CACHE_TTL_SECONDS = 60
MAX_RETRIES = 2
RETRY_DELAY = 4

# ─────────────────────────────────────────────
# UI — SIDEBAR
# ─────────────────────────────────────────────
st.title("OTPYRC")
st.markdown("Live crypto prices via the CoinGecko API.")

st.sidebar.header("🔧 Controls")

# API key input — only shown if not hardcoded above
if not API_KEY:
    api_key_input = st.sidebar.text_input(
        "🔑 CoinGecko API Key",
        type="password",
        placeholder="CG-xxxxxxxxxxxxxxxxxxxx",
        help="Free key at coingecko.com/en/api — required on Streamlit Cloud to avoid 429 errors"
    )
else:
    api_key_input = API_KEY

# Show warning if no key provided
if not api_key_input:
    st.sidebar.warning(
        "⚠️ No API key — you'll likely get 429 errors on Streamlit Cloud.\n\n"
        "Get a free key at [coingecko.com/en/api](https://www.coingecko.com/en/api)"
    )

coins = st.sidebar.text_input(
    "Coin IDs (comma separated):",
    value="bitcoin,ethereum,dogecoin"
)
currencies = st.sidebar.text_input(
    "Currencies (comma separated):",
    value="usd,inr,eur"
)

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.info(f"💡 Data cached for {CACHE_TTL_SECONDS}s to stay under rate limits.")

# ─────────────────────────────────────────────
# CACHED API CALLS
# Cache key includes the api_key so different keys get their own cache
# ─────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Fetching live prices...")
def fetch_prices(coins: str, currencies: str, api_key: str):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coins,
        "vs_currencies": currencies,
        "include_24hr_change": "true",
        "include_last_updated_at": "true"
    }
    # Demo key goes in the header, NOT as a query param
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}

    for attempt in range(MAX_RETRIES):
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return resp.json(), None
        elif resp.status_code == 429:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return None, 429
        else:
            return None, resp.status_code
    return None, 429


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Fetching 7-day trends...")
def fetch_sparklines(coins: str, api_key: str):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "ids": coins, "sparkline": "true"}
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}

    for attempt in range(MAX_RETRIES):
        resp = requests.get(url, params=params, headers=headers)
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
# FETCH
# ─────────────────────────────────────────────
price_data, price_err = fetch_prices(coins, currencies, api_key_input)
sparkline_data, spark_err = fetch_sparklines(coins, api_key_input)

ERROR_MESSAGES = {
    429: (
        "⛔ **Rate limited (429).**\n\n"
        "On Streamlit Cloud this usually means the shared IP is blocked.\n\n"
        "**Fix:** Paste your free CoinGecko API key in the sidebar.\n"
        "Get one at → https://www.coingecko.com/en/api"
    ),
    400: "❌ Bad request (400) — check coin IDs are valid CoinGecko slugs (e.g. `bitcoin`, not `BTC`).",
    500: "🔥 CoinGecko server error (500) — their problem, not yours. Try again in a minute.",
}

if price_err:
    msg = ERROR_MESSAGES.get(price_err, f"API Error {price_err} — try again later.")
    st.error(msg)
    st.stop()

# ─────────────────────────────────────────────
# PRICES TABLE
# ─────────────────────────────────────────────
df = pd.DataFrame(price_data).T

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
# SPARKLINES
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
