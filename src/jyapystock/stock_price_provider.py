"""
jyapystock: Stock price library supporting live and historical prices for Indian and American stocks.
Sources: yfinance (default), Alpha Vantage (optional)
"""

from datetime import datetime
from typing import Optional, Union, List
import os
from jyapystock.alpha_vantage_support import get_alpha_vantage_live_price, get_alpha_vantage_historical_price
from jyapystock.yfinance_support import get_yfinance_live_price, get_yfinance_historical_prices, get_yfinance_stock_info
from jyapystock.nasdaq_support import get_nasdaq_live_price, get_nasdaq_historical_prices
from jyapystock.nse_support import get_nse_live_price, get_nse_historical_prices
from jyapystock.bse_support import get_bse_live_price, get_bse_historical_prices
from jyapystock.nyse_support import get_nyse_live_price, get_nyse_historical_prices

class StockPriceProvider:
    def __init__(self, country: str, source: Optional[Union[str, List[str]]] = None, alpha_vantage_api_key: Optional[str] = None, exchange: Optional[str] = None):
        """Create a provider.

        If `source` is None or 'auto', the provider will try available free sources
        in order (yfinance first, then Alpha Vantage if an API key is provided).
        Otherwise specify `source` as a string (e.g., 'yfinance') or a list of sources (e.g., ['yfinance'] or ['alphavantage', 'yfinance']).
        """
        self.country = country.lower()
        self.check_country_validity()
        if source:
            if isinstance(source, str):
                self.source = [source.lower()]
            else:
                self.source = [s.lower() for s in source]
        else:
            self.source = ["auto"]
        self.check_source_validity()
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.exchange = exchange
        if self.exchange:
            self.exchange = self.exchange.lower()
        
        self.exchange_per_country = {
            "usa": ["nyse", "nasdaq"], 
            "india": ["nse", "bse"]
        }
        self.check_exchange_validity()
        
        self.exchange_per_source = {
            "yfinance":["nse", "bse", "nasdaq", "nyse"],
            "alphavantage":["nasdaq", "nyse"], 
            "nasdaq":["nasdaq"], 
            "nyse": ["nyse"],
            "nse":["nse"], 
            "bse":["bse"]
        }
        self.country_per_source = {
            "yfinance":["india", "usa"],
            "alphavantage":["usa"], 
            "nasdaq":["usa"], 
            "nyse": ["usa"],
            "nse":["india"], 
            "bse":["india"]
        }

    def check_source_validity(self):
        """Check if the provided source is valid."""
        valid_sources = ["yfinance", "alphavantage", "nasdaq", "nse", "bse", "nyse", "auto"]
        for s in self.source:
            if s not in valid_sources:
                raise ValueError(f"Unknown source: {s}. Valid options are: {valid_sources}")

    def check_country_validity(self):
        """Check if the provided country is valid."""
        valid_countries = ["india", "usa"]
        if self.country not in valid_countries:
            raise ValueError(f"Unknown country: {self.country}. Valid options are: {valid_countries}")
    
    def check_exchange_validity(self):
        """Check if the provided exchange is valid."""
        
        if self.exchange and self.exchange not in self.exchange_per_country[self.country]:
            raise ValueError(f"Unknown exchange: {self.exchange}. Valid options are: {self.exchange_per_country[self.country]}")
    
    def is_valid_source(self, src):
        if not self.country in self.country_per_source[src]:
            return False
        if not self.exchange:
            return True
        return self.exchange in self.exchange_per_source[src]
        
    def get_live_price(self, symbol: str) -> Optional[dict]:
        """
        Get the live price for the given symbol.
        :param symbol: Symbol to fetch the live price for
        :type symbol: str
        :return: Returns a dict with 'timestamp', 'price', and 'change_percent' (% change from previous day close),
                 or None if not available.
        :rtype: dict | None
        """
        for src in self.source:
            # yfinance first, respecting country-specific variants
            if (src == "yfinance" or src == "auto") and self.is_valid_source("yfinance"):
                val = get_yfinance_live_price(symbol, self.country, self.exchange)
                if val is not None:
                    return val
            
            # Try NSE for India stocks
            if (src == "nse" or src == "auto") and self.is_valid_source("nse"):
                val = get_nse_live_price(symbol)
                if val is not None:
                    return val
            
            # Try BSE for India stocks
            if (src == "bse" or src == "auto") and self.is_valid_source("bse"):
                val = get_bse_live_price(symbol)
                if val is not None:
                    return val
            
            # Try NASDAQ-specific provider for USA symbols
            if (src == "nasdaq" or src == "auto") and self.is_valid_source("nasdaq"):
                val = get_nasdaq_live_price(symbol, self.country)
                if val is not None:
                    return val
            
            if (src == "alphavantage" or src == "auto") and self.is_valid_source("alphavantage"):
                # Try Alpha Vantage if API key available
                av_key = self.alpha_vantage_api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
                if av_key:
                    val = get_alpha_vantage_live_price(symbol, av_key)
                    if val is not None:
                        return val

            # Try NYSE-specific provider for USA symbols
            if (src == "nyse" or src == "auto") and self.is_valid_source("nyse"):
                val = get_nyse_live_price(symbol)
                if val is not None:
                    return val
        # No sources returned a price
        return None

    def get_historical_price(self, symbol: str, start: Union[str, datetime], end: Union[str, datetime]) -> Optional[list]:
        for src in self.source:
            # yfinance first (respecting country-specific variants)
            if src == "yfinance" or src == "auto":
                val = get_yfinance_historical_prices(symbol, start, end, self.country, self.exchange)
                if val is not None:
                    return val
            
            # NSE for India stocks
            if (src == "nse" or src == "auto") and self.is_valid_source("nse"):
                val = get_nse_historical_prices(symbol, start, end)
                if val is not None:
                    return val
            
            # BSE for India stocks
            if (src == "bse" or src == "auto") and self.is_valid_source("bse"):
                val = get_bse_historical_prices(symbol, start, end)
                if val is not None:
                    return val
            
            # NASDAQ historical provider (USA)
            if (src == "nasdaq" or src == "auto") and self.is_valid_source("nasdaq"):
                val = get_nasdaq_historical_prices(symbol, start, end, self.country)
                if val is not None:
                    return val
            
            if src == "alphavantage" or src == "auto":
                av_key = self.alpha_vantage_api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
                if av_key:
                    val = get_alpha_vantage_historical_price(symbol, start, end, av_key)
                    if val is not None:
                        return val
            
            # NYSE historical provider (USA)
            if (src == "nyse" or src == "auto") and self.is_valid_source("nyse"):
                val = get_nyse_historical_prices(symbol, start, end, self.country)
                if val is not None:
                    return val
        return None

    def get_stock_info(self, symbol: str) -> Optional[dict]:
        for src in self.source:
            if src == "yfinance" or src == "auto":
                val = get_yfinance_stock_info(symbol, self.country, self.exchange)
                if val is not None:
                    return val
        return None

# Example usage:
# provider = StockPriceProvider("USA")
# price = provider.get_live_price("AAPL")
# hist = provider.get_historical_price("AAPL", "2023-01-01", "2023-01-31")
# provider_in = StockPriceProvider("India")
# price_in = provider_in.get_live_price("RELIANCE.NS")
