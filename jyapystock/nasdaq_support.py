"""
yfinance support for jyapystock
Provides helper functions to fetch live and historical prices using yfinance
and to try country-specific symbol variants (e.g., .NS/.BO for India).
"""
import codecs
import csv
import datetime
import requests
from datetime import datetime
from typing import Optional, Union
from dateutil.parser import parse


def get_nasdaq_live_price(symbol: str, country: str) -> Optional[float]:
    """
    Returns the latest close price as float, or None if not available.
    """
    if country != "usa":
        return None  # NASDAQ support only for USA
    headers =  {
                    'Accept': 'application/json, text/plain, */*',
                    'DNT': "1",
                    'Origin': 'https://www.nasdaq.com/',
                    'Sec-Fetch-Mode': 'cors',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'
                }
    urlData = "https://api.nasdaq.com/api/quote/" + symbol+ "/info?assetclass=stocks"
    etfUrlData = "https://api.nasdaq.com/api/quote/" + symbol + "/info?assetclass=etf"
    for url in [urlData, etfUrlData]:
        try:
            get_response = requests.get(urlData, headers=headers, timeout=10)
            if get_response and get_response.status_code == 200:
                json_data = get_response.json()
                data = dict()
                if 'data' in json_data:
                    if json_data['data']:
                        if 'secondaryData' in json_data['data'] and  json_data['data']['secondaryData']:
                            timestamp = json_data['data']['secondaryData']['lastTradeTimestamp']
                            if 'ON' in timestamp:
                                pos = timestamp.find('ON')
                                timestamp = timestamp[pos+3:]
                                date = datetime.datetime.strptime(timestamp, "%b %d, %Y").date()
                                return float(json_data['data']['secondaryData']['lastSalePrice'].replace('$',''))
                        if 'primaryData' in json_data['data'] and  json_data['data']['primaryData']:
                            timestamp = json_data['data']['primaryData']['lastTradeTimestamp']
                            if 'ON' in timestamp:
                                pos = timestamp.find('ON')
                                timestamp = timestamp[pos+3:]
                            if 'OF'in timestamp:
                                pos = timestamp.find('OF')
                                timestamp = timestamp[pos+3:]
                                timestamp = timestamp.replace(' ET', '')
                                timestamp = timestamp.replace(' - AFTER HOURS', '')
                            date_obj = parse(timestamp).date()
                            latest_val = json_data['data']['primaryData']['lastSalePrice']
                            return float(latest_val.replace('$',''))
        except Exception:
            continue
    return None


def get_nasdaq_historical_prices(symbol: str, start: Union[str, datetime], end: Union[str, datetime], country: str) -> Optional[list]:
    """
    Returns a list of records with Open/High/Low/Close/Volume or None if not found.
    """
    if country != "usa":
        return None  # NASDAQ support only for USA
    # Normalize start/end to datetime if they are strings
    try:
        if isinstance(start, str):
            start = parse(start)
        if isinstance(end, str):
            end = parse(end)
    except Exception:
        # If parsing fails, leave as-is and let later formatting raise if necessary
        pass
    get_response = None
    #https://api.nasdaq.com/api/quote/CSCO/historical?assetclass=stocks&fromdate=2021-02-18&limit=9999&todate=2021-02-21
    etfUrlData = f"https://api.nasdaq.com/api/quote/{symbol}/historical?assetclass=etf&fromdate={start.strftime('%Y-%m-%d')}&limit=9999&todate={end.strftime('%Y-%m-%d')}"
    urlData = f"https://api.nasdaq.com/api/quote/{symbol}/historical?assetclass=stocks&fromdate={start.strftime('%Y-%m-%d')}&limit=9999&todate={end.strftime('%Y-%m-%d')}"

    for urlData in [urlData, etfUrlData]:
        headers = {
                    'Content-Type': "application/x-www-form-urlencoded",
                    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
                    'Accept': "application/json, text/plain, */*",
                    'Origin': "https://www.nasdaq.com",
                    'accept-encoding': "gzip, deflate, br",
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': "close",
                    'cache-control': "no-cache",
                    'Referer': 'https://www.nasdaq.com/'
                }
        try:
            get_response = requests.get(urlData, headers=headers, timeout=10)
            if get_response and get_response.status_code == 200:
                json_data = get_response.json()
                if 'data' in json_data and 'tradesTable' in json_data['data']:
                    rows = json_data['data']['tradesTable']['rows']
                    records = []
                    for row in rows:
                        try:
                            cdate = datetime.strptime(row.get('date', ''), '%m/%d/%Y').date()
                            close = get_float_or_none_from_string(row.get('close'))
                            open_v = get_float_or_none_from_string(row.get('open'))
                            high = get_float_or_none_from_string(row.get('high'))
                            low = get_float_or_none_from_string(row.get('low'))
                            vol_raw = row.get('volume')
                            volume = None
                            if vol_raw:
                                try:
                                    volume = int(str(vol_raw).replace(',', '').strip())
                                except Exception:
                                    volume = None

                            records.append({
                                'date': str(cdate),
                                'Open': open_v,
                                'High': high,
                                'Low': low,
                                'Close': close,
                                'Volume': volume
                            })
                        except Exception:
                            continue

                    return records

        except Exception:
            pass
        return None
    
def get_float_or_none_from_string(input):
    if input != None and input != '':
        try:
            input = input.replace(',', '')
            input = input.replace('$', '')
            input = input.strip()
            res = float(input)
            return res
        except Exception as e:
            pass
    return None
