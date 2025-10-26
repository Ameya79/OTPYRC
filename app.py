
import streamlit as st
import requests
import pandas as pd

st.title("OTPYRC")
st.markdown("OTPYRC fetches live crypto prices using the CoinGecko API.")

st.sidebar.header("🔧 Controls")
coins = st.sidebar.text_input("Enter Coin IDs (comma separated):",value="bitcoin,ethereum,dogecoin")
currencies = st.sidebar.text_input("Enter Currencies (comma separated):",value="usd,inr,eur")

#--------------------------------------------------------

# API endpoint
url = "https://api.coingecko.com/api/v3/simple/price" # api sees this 
stored = {
    "ids": coins,        # which coin do we want
    "vs_currencies": currencies  # which currencies do we need
}

response = requests.get(url , params=stored)


if response.status_code == 200:
    data = response.json()

    df = pd.DataFrame(data)
    flipped_df = df.T # interchanges cols and rows
    
    st.write(flipped_df)
    # print("Bitcoin rate: ")
    # for coin,prices in data.items():
    #     print(f"{coin.capitalize()}: USD {prices['usd']}, INR {prices['inr']}, EUR {prices['eur']}")
    st.write("### Current Prices Chart ")
    currency_list = []
    for i in currencies.split(','):
        currency_list.append(i.strip())
    #slection box added here
    selected_currency = st.selectbox("Select currency to visualize:", currency_list)
        # check if that currency exists in your DataFrame
    if selected_currency in flipped_df.columns:
        st.bar_chart(flipped_df[selected_currency])
    else:
        st.warning("Selected currency not found in data.")
else:
    st.write("Error",response.status_code)


    








