# Alpha Vantage support for jyapystock
import os
import requests

def get_alpha_vantage_live_price(symbol: str, api_key: str) -> float:
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    try:
        price = float(data["Global Quote"]["05. price"])
        return price
    except Exception:
        return None

def get_alpha_vantage_historical_price(symbol: str, start: str, end: str, api_key: str) -> list:
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    prices = []
    try:
        ts = data["Time Series (Daily)"]
        for date, values in ts.items():
            if start <= date <= end:
                prices.append({
                    "date": date,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["6. volume"])
                })
        prices.sort(key=lambda x: x["date"])
        return prices
    except Exception:
        return []
