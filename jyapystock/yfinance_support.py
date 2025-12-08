"""
yfinance support for jyapystock
Provides helper functions to fetch live and historical prices using yfinance
and to try country-specific symbol variants (e.g., .NS/.BO for India).
"""

from datetime import datetime
from typing import Optional, Union
import yfinance as yf


def get_yfinance_live_price(symbol: str, country: str) -> Optional[float]:
    """Try live price with possible symbol variants for the given country.

    Returns the latest close price as float, or None if not available.
    """
    variants = [symbol]
    if country == "india":
        if "." not in symbol:
            variants = [f"{symbol}.NS", f"{symbol}.BO", symbol]

    for s in variants:
        try:
            ticker = yf.Ticker(s)
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data["Close"].iloc[-1])
        except Exception:
            continue
    return None


def get_yfinance_historical_prices(symbol: str, start: Union[str, datetime], end: Union[str, datetime], country: str) -> Optional[list]:
    """Try historical price retrieval with symbol variants.

    Returns a list of records with Open/High/Low/Close/Volume or None if not found.
    """
    variants = [symbol]
    if country == "india":
        if "." not in symbol:
            variants = [f"{symbol}.NS", f"{symbol}.BO", symbol]

    for s in variants:
        try:
            ticker = yf.Ticker(s)
            data = ticker.history(start=start, end=end)
            if not data.empty:
                return data[["Open", "High", "Low", "Close", "Volume"]].to_dict("records")
        except Exception:
            continue
    return None
