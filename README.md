💰 OTPYRC: Live Cryptocurrency Price Tracker

OTPYRC (Crypto spelled backward) is a simple, fast, and real-time dashboard built with Streamlit that uses the CoinGecko API to fetch and visualize live cryptocurrency prices, daily changes, and 7-day trends.

It's designed to give you a quick, clean overview of your selected digital assets.

✨ Features

Real-Time Data: Fetches up-to-the-minute prices using the CoinGecko API.

Customizable Tracking: Easily select which Coins (e.g., bitcoin, ethereum) and Currencies (e.g., usd, eur) you want to monitor using the sidebar controls.

7-Day Trends: Includes sparkline charts for each coin, showing its price movement over the last week.

24-Hour Metrics: Displays the percentage change in price over the last 24 hours, color-coded for quick visual analysis (Green for up, Red for down).

Interactive Charts: Includes bar charts for easy comparison of current prices across selected coins.

🛠️ Installation and Setup

To run OTPYRC locally, you need Python installed on your system.

1. Clone the repository (Simulated Step)

Since this is a single file, you would typically save the provided Python code as a file named otpyrc_app.py.

2. Install Dependencies

You only need two main libraries: streamlit and pandas. The requests library is usually included with Python environments.

pip install streamlit pandas


3. Run the App

Execute the Streamlit app from your terminal:

streamlit run otpyrc_app.py


The application will automatically open in your web browser, usually at http://localhost:8501.

🚀 How to Use

All the core settings for the tracker are located in the Controls section of the sidebar on the left.

1. Configure Coins and Currencies

In the sidebar, you will see two input fields:

Control Field

Description

Default Value

Enter Coin IDs

The official CoinGecko ID for the cryptocurrency. Separate multiple coins with a comma.

bitcoin,ethereum,dogecoin

Enter Currencies

The fiat currency codes (or other crypto codes) for comparison. Separate multiple currencies with a comma.

usd,inr,eur

Example: To track Cardano, Polygon, and Solana against the Japanese Yen and British Pound, you would enter:

Coin IDs: cardano,matic-network,solana

Currencies: jpy,gbp

2. Refresh Data

The CoinGecko API is very fast, but if you want to force an immediate update of all prices, just click the 🔄 Refresh Data button in the sidebar.

3. Analyze the Visualizations

Current Prices Table: Shows the raw data, including price, 24-hour change, and the last update timestamp for every coin and currency combination you selected.

Select currency to visualize: Use the dropdown menu to select one currency (e.g., usd) to focus the charts and change metrics on.

Change Metrics: A table that clearly shows the current price and the color-coded 24hr change percentage.

📈 7-Day Price Trends: A row of clean line charts (sparklines) showing the price movement over the past seven days for each selected coin.

Current Price Comparison: A simple bar chart comparing the latest price of your selected coins against the primary currency you chose in the selector.
