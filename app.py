import streamlit as st
import requests
import pandas as pd

st.title("OTPYRC")
st.markdown("OTPYRC fetches live crypto prices using the CoinGecko API.")

st.sidebar.header("🔧 Controls")
coins = st.sidebar.text_input("Enter Coin IDs (comma separated):", value="bitcoin,ethereum,dogecoin")
currencies = st.sidebar.text_input("Enter Currencies (comma separated):", value="usd,inr,eur")

#--------------------------------------------------------
# REFRESH BUTTON - Simple one-click refresh
#--------------------------------------------------------
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()  # Just refreshes the page when clicked

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
# SPARKLINE DATA (7-day mini charts)
#--------------------------------------------------------
sparkline_url = "https://api.coingecko.com/api/v3/coins/markets"
sparkline_params = {
    "vs_currency": "usd",
    "ids": coins,
    "sparkline": "true"
}
spark_response = requests.get(sparkline_url, params=sparkline_params)

# Store sparkline data in dictionary
sparkline_data = {}
if spark_response.status_code == 200:
    spark_json = spark_response.json()
    for coin_data in spark_json:
        coin_id = coin_data["id"]
        sparkline_data[coin_id] = coin_data["sparkline_in_7d"]["price"]

#--------------------------------------------------------
# PROCESS MAIN PRICE DATA
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
    # SPARKLINE CHARTS - Clean line charts showing 7-day trend
    #--------------------------------------------------------
    st.write("### 📈 7-Day Price Trends")
    
    coin_list = [c.strip().lower() for c in coins.split(',')]
    cols = st.columns(len(coin_list))
    
    for idx, coin in enumerate(coin_list):
        if coin in sparkline_data:
            with cols[idx]:
                st.markdown(f"**{coin.upper()}**")
                
                prices = sparkline_data[coin]
                spark_df = pd.DataFrame(prices, columns=['Price'])
                
                st.line_chart(spark_df, height=180, use_container_width=True)

    # Original bar chart for current prices
    if price_col in flipped_df.columns:
        st.write("### Current Price Comparison")
        st.bar_chart(flipped_df[price_col])
    else:
        st.warning("Selected currency not found in data.")

else:
    st.write("Error", response.status_code)

