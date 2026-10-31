import pytest
from unittest.mock import patch, MagicMock
from app import parse_input_list, fetch_prices, fetch_sparklines


def test_parse_input_list_clean():
    raw = "bitcoin, ethereum, solana"
    result = parse_input_list(raw)
    assert result == ["bitcoin", "ethereum", "solana"]


def test_parse_input_list_with_whitespace_and_trailing_commas():
    raw = "  bitcoin ,  ETHEREUM, ,  dogecoin , "
    result = parse_input_list(raw)
    assert result == ["bitcoin", "ethereum", "dogecoin"]


def test_parse_input_list_empty():
    assert parse_input_list("") == []
    assert parse_input_list("   , ,  ") == []
    assert parse_input_list(None) == []


def test_parse_input_list_deduplication():
    raw = "bitcoin, ethereum, bitcoin, BITCOIN"
    result = parse_input_list(raw)
    assert result == ["bitcoin", "ethereum"]


@patch("requests.get")
def test_fetch_prices_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "bitcoin": {"usd": 65000, "usd_24h_change": 2.5},
        "ethereum": {"usd": 3500, "usd_24h_change": -1.2}
    }
    mock_get.return_value = mock_resp

    data, err = fetch_prices("bitcoin,ethereum", "usd", "dummy_key")
    assert err is None
    assert "bitcoin" in data
    assert data["bitcoin"]["usd"] == 65000


@patch("requests.get")
def test_fetch_prices_rate_limit(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_get.return_value = mock_resp

    data, err = fetch_prices("bitcoin", "usd", "")
    assert err == 429
    assert data is None


@patch("requests.get")
def test_fetch_sparklines_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "id": "bitcoin",
            "sparkline_in_7d": {"price": [60000, 61000, 62000, 65000]}
        }
    ]
    mock_get.return_value = mock_resp

    spark, err = fetch_sparklines("bitcoin", "dummy_key")
    assert err is None
    assert "bitcoin" in spark
    assert len(spark["bitcoin"]) == 4
