"""
BSE (Bombay Stock Exchange of India) support for jyapystock.
Provides helper functions to fetch live and historical prices for Indian stocks.
"""

from bse import BSE
import logging
import tempfile
from typing import Optional, Union
from datetime import datetime
from dateutil.parser import parse


# Global BSE instance
_bse_instance = None


def _get_bse_instance():
    """Get or create a singleton BSE instance."""
    global _bse_instance
    if _bse_instance is None:
        temp_dir = tempfile.mkdtemp()
        _bse_instance = BSE(download_folder=temp_dir)
    return _bse_instance


def get_bse_live_price(symbol: str) -> Optional[dict]:
    """
    Fetch live quote for an Indian stock using BSE API.
    
    Returns a dict with 'timestamp', 'price', and 'change_percent', or None if not available.
    """
    try:
        bse = _get_bse_instance()
        # Convert symbol to scrip code used by BSE
        try:
            code = bse.getScripCode(symbol)
        except Exception:
            code = None
        if not code:
            # Try lookup by symbol string
            try:
                lookup = bse.lookup(symbol)
                if lookup and isinstance(lookup, dict):
                    # pick first matching code
                    first = next(iter(lookup.values()))
                    code = first.get('FinInstrmId') if isinstance(first, dict) else None
            except Exception:
                code = None

        if not code:
            return None

        # quote expects the scrip code
        result = bse.quote(code)
        if not result:
            return None

        # BSE quote returns keys like 'LTP' (last traded price) and 'PrvsClsgPric'
        last_price = result.get('LTP') or result.get('LastPric') or result.get('ClsPric')
        prev_close = result.get('PrvsClsgPric') or result.get('PrevClose')

        if last_price is None:
            return None

        # compute percent change if possible
        try:
            if prev_close:
                p_change = round(((float(last_price) - float(prev_close)) / float(prev_close)) * 100, 2)
            else:
                p_change = 0.0
        except Exception:
            p_change = 0.0

        # Use current timezone-aware UTC timestamp as BSE quote may not provide one
        from datetime import datetime as _dt, timezone as _tz
        timestamp = _dt.now(_tz.utc).isoformat()

        return {
            "timestamp": timestamp,
            "price": float(last_price),
            "change_percent": p_change
        }
    except Exception:
        return None


def get_bse_historical_prices(symbol: str, start: Union[str, datetime], end: Union[str, datetime]) -> Optional[list]:
    """
    Fetch historical prices for an Indian stock from BSE.
    
    `start` and `end` may be strings (ISO like '2023-01-01') or datetime objects.
    Returns a list of records with date/open/high/low/close/volume, or None if not available.
    """
    try:
        # Normalize start/end to date objects
        if isinstance(start, str):
            start_dt = parse(start).date()
        elif isinstance(start, datetime):
            start_dt = start.date()
        else:
            start_dt = start

        if isinstance(end, str):
            end_dt = parse(end).date()
        elif isinstance(end, datetime):
            end_dt = end.date()
        else:
            end_dt = end

        bse = _get_bse_instance()

        # Resolve symbol to FinInstrmId (scrip code)
        try:
            code = bse.getScripCode(symbol)
        except Exception:
            code = None

        records = []
        # iterate through each date in range inclusive
        curr = start_dt
        import pandas as _pd
        from datetime import timedelta as _td
        while curr <= end_dt:
            try:
                path = bse.bhavcopyReport(curr)
                if path is None:
                    curr = curr + _td(days=1)
                    continue
                df = _pd.read_csv(path)
                # Try to find by FinInstrmId or ticker symbol
                if code is not None and 'FinInstrmId' in df.columns:
                    match = df[df['FinInstrmId'] == int(code)]
                else:
                    # fallback to ticker symbol column
                    if 'TckrSymb' in df.columns:
                        match = df[df['TckrSymb'].str.upper() == symbol.upper()]
                    else:
                        match = _pd.DataFrame()

                if not match.empty:
                    # take first matching row
                    row = match.iloc[0]
                    records.append({
                        'date': change_date_format(str(row.get('TradDt', curr.isoformat()))),
                        'open': float(row.get('OpnPric') or row.get('OpnPr') or 0.0),
                        'high': float(row.get('HghPric') or 0.0),
                        'low': float(row.get('LwPric') or 0.0),
                        'close': float(row.get('ClsPric') or row.get('LastPric') or row.get('SttlmPric') or 0.0),
                        'volume': float(row.get('TtlTradgVol') or row.get('TtlTrfVal') or 0.0)
                    })
            except Exception:
                # ignore date-specific failures and continue
                pass
            curr = curr + _td(days=1)

        return records if records else None
    except Exception as e:
        logging.error(f"Error fetching historical prices for {symbol} from BSE: {str(e)}")
        return None

def change_date_format(date_str: str) -> str:
    """Convert date to 'yyyy-mm-dd' format."""
    try:
        dt = parse(date_str).date()
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        logging.error(f"Error converting date format: {str(e)}")
        return date_str  # Return original if conversion fails
