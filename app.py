"""
OTPYRC: Live Cryptocurrency Price Tracker
Enhanced with Streamlit Native Metrics, Multi-Tab Layout, Rate-Limit Resilient Fetching,
and Environment-Driven Configuration.
"""

import os
import time
from typing import List, Tuple, Dict, Any, Optional
import streamlit as st
import requests
import pandas as pd

# Load environment variable defaults if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ENV_API_KEY = os.environ.get("COINGECKO_API_KEY", "")
CACHE_TTL_SECONDS = 60
MAX_RETRIES = 2
RETRY_DELAY = 3

st.set_page_config(
    page_title="OTPYRC - Live Crypto Tracker",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def parse_input_list(raw_input: str) -> List[str]:
    """Parse comma-separated values into a clean, deduplicated lowercase list."""
    if not raw_input or not isinstance(raw_input, str):
        return []
    items = [item.strip().lower() for item in raw_input.split(",") if item.strip()]
    return list(dict.fromkeys(items))  # Preserves order while removing duplicates


# ─────────────────────────────────────────────
# UI — SIDEBAR CONTROLS
# ─────────────────────────────────────────────

st.sidebar.title("🪙 OTPYRC Controls")
st.sidebar.caption("Real-Time Cryptocurrency Market Monitor")

# API Key handling: env var -> user input override
api_key_input = st.sidebar.text_input(
    "🔑 CoinGecko API Key",
    value=ENV_API_KEY,
    type="password",
    placeholder="CG-xxxxxxxxxxxxxxxxxxxx",
    help="Free API key from coingecko.com/en/api — helps avoid 429 rate limits."
)

if not api_key_input:
    st.sidebar.warning(
        "⚠️ No API key set. Free tier rate limits (30 req/min) apply.\n\n"
        "Get a free demo key at [coingecko.com/en/api](https://www.coingecko.com/en/api)"
    )

coins_input = st.sidebar.text_input(
    "Coin Slugs (comma separated):",
    value="bitcoin, ethereum, solana, dogecoin",
    help="Valid CoinGecko slug IDs (e.g., 'bitcoin', 'ethereum', NOT ticker symbols like 'BTC')."
)

currencies_input = st.sidebar.text_input(
    "Currencies (comma separated):",
    value="usd, inr, eur",
    help="Target fiat or crypto currencies to compare against."
)

st.sidebar.markdown("---")

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col_sb2:
    auto_refresh = st.checkbox("Auto-refresh", value=False)

st.sidebar.info(f"💡 Cache TTL: {CACHE_TTL_SECONDS}s to preserve API quotas.")

# ─────────────────────────────────────────────
# CACHED API CALLS
# ─────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Fetching latest market prices...")
def fetch_prices(coins_str: str, currencies_str: str, api_key: str) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    """Fetch spot prices and 24h change percentages from CoinGecko."""
    if not coins_str or not currencies_str:
        return {}, None

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coins_str,
        "vs_currencies": currencies_str,
        "include_24hr_change": "true",
        "include_last_updated_at": "true"
    }
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                return resp.json(), None
            elif resp.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    return None, 429
            else:
                return None, resp.status_code
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return None, 503
    return None, 429


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Fetching 7-day sparkline trends...")
def fetch_sparklines(coins_str: str, api_key: str) -> Tuple[Dict[str, List[float]], Optional[int]]:
    """Fetch 7-day sparkline history for each requested coin."""
    if not coins_str:
        return {}, None

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "ids": coins_str, "sparkline": "true"}
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                result = {}
                for coin_data in resp.json():
                    cid = coin_data.get("id")
                    spark = coin_data.get("sparkline_in_7d", {}).get("price", [])
                    if cid and spark:
                        result[cid] = spark
                return result, None
            elif resp.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    return {}, 429
            else:
                return {}, resp.status_code
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return {}, 503
    return {}, 429


# ─────────────────────────────────────────────
# MAIN APPLICATION LOGIC
# ─────────────────────────────────────────────

coins_list = parse_input_list(coins_input)
currencies_list = parse_input_list(currencies_input)

st.title("🪙 OTPYRC: Live Cryptocurrency Dashboard")
st.caption("Real-time cryptocurrency analytics, sparkline trends, and cross-currency comparisons.")

if not coins_list or not currencies_list:
    st.warning("⚠️ Please provide at least one valid coin slug and one target currency in the sidebar.")
    st.stop()

coins_param = ",".join(coins_list)
currencies_param = ",".join(currencies_list)

price_data, price_err = fetch_prices(coins_param, currencies_param, api_key_input)
sparkline_data, spark_err = fetch_sparklines(coins_param, api_key_input)

# Error Handling Display
ERROR_MESSAGES = {
    429: (
        "⛔ **Rate Limited (HTTP 429)**: CoinGecko request limit reached. "
        "Please provide a free Demo API Key in the sidebar or wait a minute before refreshing."
    ),
    400: "❌ **Bad Request (HTTP 400)**: One or more coin slugs are invalid. Check coin slugs at coingecko.com.",
    500: "🔥 **CoinGecko Server Error (HTTP 500)**: Upstream service error. Please retry shortly.",
    503: "📡 **Network Timeout (HTTP 503)**: Failed to connect to CoinGecko. Check internet connection."
}

if price_err:
    msg = ERROR_MESSAGES.get(price_err, f"API Error: HTTP {price_err}")
    st.error(msg)
    st.stop()

if not price_data:
    st.info("No pricing data returned. Ensure the coin slugs are valid (e.g. 'bitcoin', 'ethereum').")
    st.stop()

# ─────────────────────────────────────────────
# TOP REAL-TIME METRICS CARDS
# ─────────────────────────────────────────────

st.subheader("⚡ Live Snapshot (USD)")
metric_cols = st.columns(min(len(coins_list), 4))
for idx, coin in enumerate(coins_list[:4]):
    coin_info = price_data.get(coin, {})
    usd_price = coin_info.get("usd")
    change_24h = coin_info.get("usd_24h_change")

    with metric_cols[idx]:
        if usd_price is not None:
            price_formatted = f"${usd_price:,.2f}" if usd_price >= 1 else f"${usd_price:.6f}"
            delta_formatted = f"{change_24h:+.2f}%" if change_24h is not None else None
            st.metric(
                label=coin.replace("-", " ").title(),
                value=price_formatted,
                delta=delta_formatted
            )
        else:
            st.metric(label=coin.replace("-", " ").title(), value="N/A")

st.markdown("---")

# ─────────────────────────────────────────────
# MULTI-TAB DISPLAY
# ─────────────────────────────────────────────

tab_overview, tab_trends, tab_compare, tab_diagnostics = st.tabs([
    "📊 Market Overview",
    "📈 7-Day Sparkline Trends",
    "⚖️ Asset Comparison",
    "ℹ️ API & Rate Limits"
])

# TAB 1: MARKET OVERVIEW
with tab_overview:
    df = pd.DataFrame(price_data).T
    
    # Filter columns to only show base prices
    price_cols_only = [
        col for col in df.columns
        if not col.endswith("_24h_change") and not col.endswith("last_updated_at")
    ]
    
    col_t1, col_t2 = st.columns([3, 2])
    
    with col_t1:
        st.markdown("#### Spot Prices Table")
        st.dataframe(df[price_cols_only], use_container_width=True)
    
    with col_t2:
        st.markdown("#### Focus Currency Metrics")
        selected_curr = st.selectbox("Select currency:", currencies_list, key="overview_curr_select")
        
        p_col = selected_curr
        c_col = f"{selected_curr}_24h_change"
        
        if p_col in df.columns:
            focus_df = df[[p_col]].copy()
            if c_col in df.columns:
                focus_df["24h Change (%)"] = pd.to_numeric(df[c_col], errors="coerce").round(2)
            focus_df = focus_df.rename(columns={p_col: f"Price ({selected_curr.upper()})"})
            st.dataframe(focus_df, use_container_width=True)
        else:
            st.warning(f"Currency '{selected_curr}' not present in response.")

# TAB 2: 7-DAY SPARKLINE TRENDS
with tab_trends:
    st.markdown("#### 7-Day Price Trends in USD")
    if spark_err:
        st.warning(f"Sparkline trend data currently unavailable (Error code: {spark_err}).")
    elif not sparkline_data:
        st.info("No sparkline records available for the requested coins.")
    else:
        trend_cols = st.columns(min(len(coins_list), 3))
        for idx, coin in enumerate(coins_list):
            col_target = trend_cols[idx % min(len(coins_list), 3)]
            with col_target:
                st.markdown(f"**{coin.upper()}**")
                if coin in sparkline_data:
                    prices = sparkline_data[coin]
                    spark_df = pd.DataFrame(prices, columns=["Price (USD)"])
                    st.line_chart(spark_df, height=180, use_container_width=True)
                    st.caption(f"Min: ${min(prices):,.2f} &bull; Max: ${max(prices):,.2f}")
                else:
                    st.info(f"No trend history for {coin}")

# TAB 3: ASSET COMPARISON
with tab_compare:
    st.markdown("#### Comparative Price Distribution")
    comp_curr = st.selectbox("Compare prices in:", currencies_list, key="compare_curr_select")
    if comp_curr in df.columns:
        bar_series = pd.to_numeric(df[comp_curr], errors="coerce")
        st.bar_chart(bar_series, use_container_width=True)
    else:
        st.warning(f"Currency '{comp_curr}' not available for comparison.")

# TAB 4: API & RATE LIMITS
with tab_diagnostics:
    st.markdown("#### CoinGecko API Diagnostics")
    st.markdown(f"""
    - **Endpoint Used**: `https://api.coingecko.com/api/v3/simple/price`
    - **Active Coins Tracked**: `{', '.join(coins_list)}`
    - **Active Currencies**: `{', '.join(currencies_list)}`
    - **API Key Mode**: `{'Demo Key Configured ✅' if api_key_input else 'Public Shared Tier ⚠️'}`
    - **Cache Window**: `{CACHE_TTL_SECONDS} seconds`
    - **Retry Strategy**: `{MAX_RETRIES} attempts with exponential backoff`
    """)

    st.markdown("---")
    st.markdown("##### Need higher rate limits?")
    st.markdown("Obtain a free Demo Key (30 req/min) at [CoinGecko Developer Portal](https://www.coingecko.com/en/api).")
