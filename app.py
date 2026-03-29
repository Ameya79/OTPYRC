"""
OTPYRC - Live Crypto Price Tracker
====================================
Uses the FREE CoinGecko API (no API key needed).
Fetches live prices, 24hr change %, and 7-day sparkline charts.

HOW TO RUN:
    pip install streamlit requests pandas
    streamlit run app.py

FUTURE REF / REMINDERS:
    - CoinGecko free tier has rate limits (~10-30 calls/min). Don't spam refresh.
    - Coin IDs must match CoinGecko slugs: e.g. "bitcoin", "ethereum", NOT "BTC"
      → Find valid IDs at: https://api.coingecko.com/api/v3/coins/list
    - Sparkline data is always in USD from CoinGecko (limitation of their free API)
    - If you get a 429 error, you've hit the rate limit. Wait ~60 seconds.
    - st.rerun() replaced the old st.experimental_rerun() in newer Streamlit versions.
      If it breaks, try: import streamlit as st; st.experimental_rerun()
    - iloc-based assignment on a copy of a df gives SettingWithCopyWarning.
      Using .loc[] is the proper fix (already done below).
"""

import streamlit as st
import requests
import pandas as pd

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.title("OTPYRC")
st.markdown("OTPYRC fetches live crypto prices using the CoinGecko API.")

# ─────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────
st.sidebar.header("🔧 Controls")

# REMINDER: Coin IDs are CoinGecko slugs (lowercase, hyphenated for multi-word coins)
# e.g. "shiba-inu", "avalanche-2", "matic-network"
coins = st.sidebar.text_input(
    "Enter Coin IDs (comma separated):",
    value="bitcoin,ethereum,dogecoin"
)

# REMINDER: Currency codes are standard ISO codes in lowercase
# e.g. "usd", "inr", "eur", "gbp", "jpy"
currencies = st.sidebar.text_input(
    "Enter Currencies (comma separated):",
    value="usd,inr,eur"
)

st.sidebar.markdown("---")

# ─────────────────────────────────────────────
# REFRESH BUTTON
# FIX: The original code had no indented body inside the if-block.
# Python requires at least one statement inside every if/else/for/while block.
# st.rerun() was there but NOT indented, so Python threw IndentationError.
# ─────────────────────────────────────────────
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()  # Reruns the entire script from top = acts as a manual refresh

# ─────────────────────────────────────────────
# API CALL 1 — LIVE PRICES
# Endpoint: /simple/price
# Returns: current price + 24hr change % for each coin/currency pair
# ─────────────────────────────────────────────
url = "https://api.coingecko.com/api/v3/simple/price"
params = {
    "ids": coins,
    "vs_currencies": currencies,
    "include_24hr_change": "true",
    "include_last_updated_at": "true"
}
response = requests.get(url, params=params)

# ─────────────────────────────────────────────
# API CALL 2 — SPARKLINE DATA (7-day mini charts)
# Endpoint: /coins/markets
# Returns: array of hourly prices for last 7 days per coin (always in USD)
# REMINDER: sparkline is always USD on free tier — can't change this currency
# ─────────────────────────────────────────────
sparkline_url = "https://api.coingecko.com/api/v3/coins/markets"
sparkline_params = {
    "vs_currency": "usd",
    "ids": coins,
    "sparkline": "true"
}
spark_response = requests.get(sparkline_url, params=sparkline_params)

# Parse sparkline into a dict: { "bitcoin": [price1, price2, ...], ... }
sparkline_data = {}
if spark_response.status_code == 200:
    for coin_data in spark_response.json():
        coin_id = coin_data["id"]
        sparkline_data[coin_id] = coin_data["sparkline_in_7d"]["price"]

# ─────────────────────────────────────────────
# PROCESS & DISPLAY MAIN PRICE DATA
# ─────────────────────────────────────────────
if response.status_code == 200:
    data = response.json()

    # CoinGecko returns: { "bitcoin": { "usd": 60000, "usd_24h_change": 2.3, ... }, ... }
    # pd.DataFrame(data) → columns = coin names, rows = price keys
    # .T (transpose) → rows = coin names, columns = price keys  ← what we want
    df = pd.DataFrame(data)
    flipped_df = df.T

    # ── Table: show only raw price columns (hide change% and timestamp cols) ──
    price_cols_only = [
        col for col in flipped_df.columns
        if not col.endswith("_24h_change") and not col.endswith("last_updated_at")
    ]

    st.write("### Current Prices Table")
    st.dataframe(flipped_df[price_cols_only])

    # ── Currency selector for the metrics + bar chart below ──
    currency_list = [c.strip().lower() for c in currencies.split(",")]
    selected_currency = st.selectbox("Select currency to visualize:", currency_list)

    price_col = selected_currency
    change_col = selected_currency + "_24h_change"

    # Guard: if change column missing (e.g. API hiccup), add empty column
    if change_col not in flipped_df.columns:
        flipped_df[change_col] = pd.NA

    if price_col in flipped_df.columns:
        # Make a clean working copy with just the two columns we need
        clean_df = flipped_df[[price_col, change_col]].copy()
        clean_df[price_col] = pd.to_numeric(clean_df[price_col], errors="coerce")
        clean_df[change_col] = pd.to_numeric(clean_df[change_col], errors="coerce")

        clean_df = clean_df.rename(columns={
            price_col: "Price",
            change_col: "24hr change"
        })

        # ── Colour-code the 24hr change column as HTML ──
        # FIX: Use .loc[] instead of .iloc[] to avoid SettingWithCopyWarning.
        # REMINDER: Never chain iloc[i] on a copy — pandas can't track it back
        #           to the original df, so the assignment silently fails sometimes.
        for coin_name in clean_df.index:
            value = clean_df.loc[coin_name, "24hr change"]
            if pd.notna(value):
                rounded = round(float(value), 2)
                if rounded >= 0:
                    clean_df.loc[coin_name, "24hr change"] = (
                        f"<span style='color:green;font-weight:bold'>+{rounded}%</span>"
                    )
                else:
                    clean_df.loc[coin_name, "24hr change"] = (
                        f"<span style='color:red;font-weight:bold'>{rounded}%</span>"
                    )
            else:
                clean_df.loc[coin_name, "24hr change"] = "N/A"

        st.write("### Change Metrics")
        clean_df = clean_df.reset_index().rename(columns={"index": "coin"})
        # unsafe_allow_html=True needed to render the <span> colour tags
        st.markdown(clean_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    else:
        st.warning("Selected currency not found in data.")

    # ─────────────────────────────────────────────
    # SPARKLINE CHARTS — 7-Day Trend Lines
    # REMINDER: One chart per coin, displayed side-by-side using st.columns()
    # ─────────────────────────────────────────────
    st.write("### 📈 7-Day Price Trends (USD)")

    coin_list = [c.strip().lower() for c in coins.split(",")]
    cols = st.columns(len(coin_list))

    for idx, coin in enumerate(coin_list):
        if coin in sparkline_data:
            with cols[idx]:
                st.markdown(f"**{coin.upper()}**")
                spark_df = pd.DataFrame(sparkline_data[coin], columns=["Price"])
                st.line_chart(spark_df, height=180, use_container_width=True)

    # ── Bar chart: current price comparison across coins ──
    if price_col in flipped_df.columns:
        st.write("### Current Price Comparison")
        # REMINDER: bar_chart needs a Series or single-column DataFrame.
        # flipped_df[price_col] gives a Series with coin names as index — perfect.
        bar_data = pd.to_numeric(flipped_df[price_col], errors="coerce")
        st.bar_chart(bar_data)
    else:
        st.warning("Selected currency not found in data.")

else:
    # Show the HTTP error code so you know what went wrong
    # 429 = rate limited | 400 = bad coin ID | 500 = CoinGecko server issue
    st.error(f"API Error {response.status_code} — check coin IDs or try again later.")
