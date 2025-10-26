import streamlit as st
import requests
import pandas as pd

st.title("OTPYRC")
st.markdown("OTPYRC fetches live crypto prices using the CoinGecko API.")

st.sidebar.header("🔧 Controls")
coins = st.sidebar.text_input("Enter Coin IDs (comma separated):", value="bitcoin,ethereum,dogecoin")
currencies = st.sidebar.text_input("Enter Currencies (comma separated):", value="usd,inr,eur")

#--------------------------------------------------------

# API endpoint
url = "https://api.coingecko.com/api/v3/simple/price"  # CoinGecko API endpoint for simple price
stored = {
    "ids": coins,                     # which coins we want prices for
    "vs_currencies": currencies,      # which currencies we want to see
    "include_24hr_change": "true",    # include 24hr price change
    "include_last_updated_at": "true" # we requested it but will not use now
}

# Make the API request
response = requests.get(url, params=stored)

if response.status_code == 200:
    data = response.json()  # Converts API JSON → Python dictionary for pandas

    # Create DataFrame from dictionary
    df = pd.DataFrame(data)

    # Transpose: coins become rows, currencies + extra fields become columns
    flipped_df = df.T

    # .T (transpose) works because every value inside is numeric and rectangular.
    # If even one inner dictionary was missing a key, pandas would insert NaN automatically.

    # ----------------------
    # Show only price columns (filter out 24h_change and last_updated_at)
    # We only want to show clean prices in the main table
    what_i_want_to_show = []
    for col in flipped_df.columns:
        if not col.endswith("_24h_change") and not col.endswith("_last_updated_at"):
            what_i_want_to_show.append(col)

    st.write("### Current Prices Table")
    st.dataframe(flipped_df[what_i_want_to_show])
    # Above: displays a table with only the base prices (USD, INR, EUR, etc.)
    # without any extra change or timestamp columns

    # ----------------------
    # Build explicit currency list for selector
    currency_list = []
    for i in currencies.split(','):
        currency_list.append(i.strip().lower())  # normalize to lowercase for consistency

    # Single selection box for chart & metrics
    selected_currency = st.selectbox("Select currency to visualize:", currency_list)

    # Build column names for selected currency
    price_col = selected_currency
    change_col = selected_currency + "_24h_change"
    # time_col removed completely

    # Ensure 24h change column exists to prevent KeyError
    if change_col not in flipped_df.columns:
        flipped_df[change_col] = pd.NA  # If the API didn't return it, fill with NA

    # Check if the price column exists
    if price_col in flipped_df.columns:
        # Create clean DataFrame explicitly
        clean_df = flipped_df[[price_col, change_col]].copy()

        # Convert numeric fields safely (just in case API returns strings)
        clean_df[price_col] = pd.to_numeric(clean_df[price_col], errors="coerce")
        clean_df[change_col] = pd.to_numeric(clean_df[change_col], errors="coerce")

        # Rename columns for human-friendly display BEFORE applying + / - formatting
        clean_df = clean_df.rename(columns={
            price_col: "Price",
            change_col: "24hr change"
        })

        # ----------------------
        # Step 1: Go through each value in the "24hr change" column
        # Step 2: Add + for positive numbers, keep - for negative, N/A if missing
        for i in range(len(clean_df)):
            value = clean_df["24hr change"].iloc[i]  # safe now because column exists
            if pd.notna(value):  # make sure it’s a number
                if value >= 0:
                    clean_df["24hr change"].iloc[i] = f"<span style='color:green;font-weight:bold'>+{round(value, 2)}%</span>"
                else:
                    clean_df["24hr change"].iloc[i] = f"<span style='color:red;font-weight:bold'>{round(value, 2)}%</span>"
            else:
                clean_df["24hr change"].iloc[i] = "N/A"

        # Display the metrics table (now only Price + 24hr change with signs)
        st.write("### Change Metrics")
        # Reset index so coin names appear as a column with header 'coin'
        clean_df = clean_df.reset_index().rename(columns={'index': 'coin'})
        # Render HTML so the <span> color tags are applied; do not show index twice
        st.markdown(clean_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning("Selected currency not found in data.")

    # ----------------------
    # Chart the prices for selected currency
    if price_col in flipped_df.columns:
        st.write("### Price Chart")
        st.bar_chart(flipped_df[price_col])
    else:
        st.warning("Selected currency not found in data.")

else:
    st.write("Error", response.status_code)
