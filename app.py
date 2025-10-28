import streamlit as st
import requests
import pandas as pd
import time

st.title("OTPYRC")
st.markdown("OTPYRC fetches live crypto prices using the CoinGecko API.")

st.sidebar.header("🔧 Controls")
coins = st.sidebar.text_input("Enter Coin IDs (comma separated):", value="bitcoin,ethereum,dogecoin")
currencies = st.sidebar.text_input("Enter Currencies (comma separated):", value="usd,inr,eur")

#--------------------------------------------------------
# NEW FEATURE 1: AUTO-REFRESH TOGGLE
# This checkbox lets users turn on/off automatic page refresh every 60 seconds
#--------------------------------------------------------
st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (60s)", value=False)

if auto_refresh:
    # Display countdown timer
    placeholder = st.sidebar.empty()
    for i in range(60, 0, -1):
        placeholder.write(f"⏱️ Refreshing in {i}s")
        time.sleep(1)
    st.rerun()  # Triggers page refresh after 60 seconds

#--------------------------------------------------------
# ORIGINAL API CALL - Simple Price Data
#--------------------------------------------------------
url = "https://api.coingecko.com/api/v3/simple/price"
stored = {
    "ids": coins,
    "vs_currencies": currencies,
    "include_24hr_change": "true",
    "include_last_updated_at": "true"
}

response = requests.get(url, params=stored)

#--------------------------------------------------------
# NEW FEATURE 2: SPARKLINE DATA (7-day mini charts)
# This is a DIFFERENT API endpoint that gives us historical price data for charts
#--------------------------------------------------------
sparkline_url = "https://api.coingecko.com/api/v3/coins/markets"
sparkline_params = {
    "vs_currency": "usd",  # Sparklines only work with one currency at a time
    "ids": coins,
    "sparkline": "true"  # This tells API to include 7-day price history
}
spark_response = requests.get(sparkline_url, params=sparkline_params)

# Store sparkline data in a dictionary for easy lookup later
# Format: {"bitcoin": [price1, price2, ...], "ethereum": [price1, price2, ...]}
sparkline_data = {}
if spark_response.status_code == 200:
    spark_json = spark_response.json()
    for coin_data in spark_json:
        coin_id = coin_data["id"]
        # sparkline_in_7d is a nested dictionary with "price" key containing list of prices
        sparkline_data[coin_id] = coin_data["sparkline_in_7d"]["price"]

#--------------------------------------------------------
# PROCESS MAIN PRICE DATA (same as before)
#--------------------------------------------------------
if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)
    flipped_df = df.T

    # Filter to show only price columns
    what_i_want_to_show = []
    for col in flipped_df.columns:
        if not col.endswith("_24h_change") and not col.endswith("last_updated_at"):
            what_i_want_to_show.append(col)

    st.write("### Current Prices Table")
    st.dataframe(flipped_df[what_i_want_to_show])

    # Build currency list for selector
    currency_list = []
    for i in currencies.split(','):
        currency_list.append(i.strip().lower())

    selected_currency = st.selectbox("Select currency to visualize:", currency_list)

    price_col = selected_currency
    change_col = selected_currency + "_24h_change"

    if change_col not in flipped_df.columns:
        flipped_df[change_col] = pd.NA

    if price_col in flipped_df.columns:
        clean_df = flipped_df[[price_col, change_col]].copy()
        clean_df[price_col] = pd.to_numeric(clean_df[price_col], errors="coerce")
        clean_df[change_col] = pd.to_numeric(clean_df[change_col], errors="coerce")

        clean_df = clean_df.rename(columns={
            price_col: "Price",
            change_col: "24hr change"
        })

        # Format 24hr change with colors
        for i in range(len(clean_df)):
            value = clean_df["24hr change"].iloc[i]
            if pd.notna(value):
                if value >= 0:
                    clean_df["24hr change"].iloc[i] = f"<span style='color:green;font-weight:bold'>+{round(value, 2)}%</span>"
                else:
                    clean_df["24hr change"].iloc[i] = f"<span style='color:red;font-weight:bold'>{round(value, 2)}%</span>"
            else:
                clean_df["24hr change"].iloc[i] = "N/A"

        st.write("### Change Metrics")
        clean_df = clean_df.reset_index().rename(columns={'index': 'coin'})
        st.markdown(clean_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning("Selected currency not found in data.")

    #--------------------------------------------------------
    # NEW FEATURE 3: SPARKLINE CHARTS DISPLAY
    # Show mini 7-day trend chart for each coin
    #--------------------------------------------------------
    st.write("### 7-Day Price Trends")
    
    # Loop through each coin and display its sparkline chart
    for coin in coins.split(','):
        coin = coin.strip().lower()
        if coin in sparkline_data:
            st.write(f"**{coin.title()}**")  # Display coin name as title
            
            # Create a DataFrame from the price list for charting
            # sparkline_data[coin] is a list of ~168 prices (7 days × 24 hours)
            spark_df = pd.DataFrame(sparkline_data[coin], columns=["Price"])
            
            # st.line_chart() creates a smooth line chart
            st.line_chart(spark_df, height=150)  # height=150 keeps it compact

    # Original bar chart for current prices
    if price_col in flipped_df.columns:
        st.write("### Price Chart")
        st.bar_chart(flipped_df[price_col])
    else:
        st.warning("Selected currency not found in data.")

else:
    st.write("Error", response.status_code)
