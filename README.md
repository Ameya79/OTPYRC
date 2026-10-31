# 🪙 OTPYRC: Live Cryptocurrency Price Tracker

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/pytest-passing-success.svg?logo=pytest&logoColor=white)](https://pytest.org/)
[![CoinGecko API](https://img.shields.io/badge/CoinGecko-v3-8DC63F.svg?logo=coingecko&logoColor=white)](https://www.coingecko.com/en/api)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

**OTPYRC** (*Crypto* spelled backward) is a modern, real-time cryptocurrency market monitoring application built with **Streamlit** and the **CoinGecko API**. It enables investors and developers to inspect live spot prices, percentage changes, 7-day sparkline charts, and relative portfolio comparisons with built-in caching, exponential backoff, and containerization.

---

## ✨ Features

- ⚡ **Live Snapshot Metric Cards**: High-level overview displaying current prices and color-coded 24-hour delta percentages.
- 📑 **Organized Multi-Tab Interface**:
  - 📊 **Market Overview**: Tabular view of prices and customizable focus currency metrics.
  - 📈 **7-Day Sparkline Trends**: Interactive trend lines in USD with min/max range indicators.
  - ⚖️ **Asset Comparison**: Comparative bar charts for cross-currency price evaluation.
  - ℹ️ **API & Rate Limits**: Diagnostics panel showing endpoint status, cache TTL, and active keys.
- 🛡️ **Rate-Limit Resilience**:
  - Streamlit caching (`ttl=60s`) keeps requests well within CoinGecko's 30 calls/min limit.
  - Exponential backoff retry strategy for handling HTTP 429 rate limit responses.
  - Headless API key ingestion via environment variables (`COINGECKO_API_KEY`) and sidebar controls.
- 🧹 **Robust Input Parsing**: Handles trailing commas, mixed casing, and extraneous whitespace gracefully.
- 🐳 **Production Docker & Docker Compose**: Single-command startup with built-in healthchecks.
- 🧪 **Automated Pytest Coverage**: Unit tests verifying token parsing, error handling, and API integration.

---

## 🚀 Quickstart

### Option 1: Run with Docker Compose (Recommended)

Make sure you have [Docker](https://docs.docker.com/get-docker/) installed:

```bash
# Clone the repository
git clone https://github.com/Ameya79/OTPYRC.git
cd OTPYRC

# Launch with Docker Compose
docker compose up -d
```

Navigate to:
👉 **[http://localhost:8501](http://localhost:8501)**

To stop the container:
```bash
docker compose down
```

---

### Option 2: Run Locally with Python

**Prerequisites:** Python 3.10+ and `pip`

```bash
# 1. Clone the repository
git clone https://github.com/Ameya79/OTPYRC.git
cd OTPYRC

# 2. (Optional) Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Streamlit application
streamlit run app.py
```

The application will launch in your default web browser at `http://localhost:8501`.

---

## ⚙️ Configuration & Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `COINGECKO_API_KEY` | Optional Demo or Pro API Key from CoinGecko | *(None / Public)* |
| `STREAMLIT_SERVER_PORT` | Port for the Streamlit web server | `8501` |
| `STREAMLIT_SERVER_HEADLESS` | Run in non-interactive headless mode | `true` |

> [!TIP]
> A free demo key (30 calls/minute) can be generated at [coingecko.com/en/api](https://www.coingecko.com/en/api). Providing this key prevents 429 rate limit blocks on shared IP addresses.

---

## 🧪 Running Tests

Execute the automated test suite using `pytest`:

```bash
pytest tests/ -v
```

Tests cover:
- Token normalization & whitespace stripping
- Deduplication of input coin IDs
- Rate limit handling (HTTP 429 backoff)
- Successful price parsing and sparkline mapping

---

## 📂 Project Structure

```
OTPYRC/
├── app.py                  # Core Streamlit application & API connectors
├── requirements.txt        # Python library dependencies
├── Dockerfile              # Production container build
├── docker-compose.yml      # Service orchestration & healthcheck
├── .dockerignore           # Container build ignore rules
├── .env.example            # Environment variables template
├── README.md               # Standardized documentation
└── tests/
    └── test_otpyrc.py      # Automated Pytest test suite
```

---

## 📜 License

Licensed under the [MIT License](LICENSE).
