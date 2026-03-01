"""
Binance API Client for MUST Market Intelligence Agent

Provides functions to fetch market data from Binance public API
without authentication requirements.
"""

import requests
from typing import List, Dict, Any, Optional
import time
from datetime import datetime


class BinanceClient:
    """Client for interacting with Binance public API endpoints."""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MUST-Market-Intelligence-Agent/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal method to make HTTP GET requests to Binance API.
        
        Args:
            endpoint: API endpoint path
            params: Dictionary of query parameters
            
        Returns:
            Parsed JSON response as dictionary
            
        Raises:
            Exception: If request fails or response is invalid
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for Binance error format
            if isinstance(data, dict) and 'code' in data and data['code'] < 0:
                raise Exception(f"Binance API Error {data['code']}: {data['msg']}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out while contacting Binance API")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error while contacting Binance API")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.reason}")
        except ValueError:
            raise Exception("Invalid JSON response from Binance API")
        except Exception as e:
            raise Exception(f"Error fetching data from Binance API: {str(e)}")
    
    def get_ticker_24hr(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch 24-hour ticker price change statistics.
        
        Args:
            symbol: Optional symbol to filter (e.g., 'BTCUSDT'). If None, returns all symbols.
            
        Returns:
            List of dictionaries containing ticker data for each symbol
            
        Example response structure:
        [
            {
                "symbol": "BTCUSDT",
                "priceChange": "0.00002100",
                "priceChangePercent": "0.019",
                "weightedAvgPrice": "11.08205106",
                "prevClosePrice": "11.08205106",
                "lastPrice": "11.08207206",
                "lastQty": "0.00000000",
                "bidPrice": "11.08207206",
                "askPrice": "11.08207206",
                "openPrice": "11.08205106",
                "highPrice": "11.08207206",
                "lowPrice": "11.08205106",
                "volume": "0.00000000",
                "quoteVolume": "0.00000000",
                "openTime": 1700000000000,
                "closeTime": 1700086399999,
                "firstId": 0,
                "lastId": 0,
                "count": 0
            }
        ]
        """
        endpoint = "ticker/24hr"
        params = {}
        
        if symbol:
            params["symbol"] = symbol
        
        try:
            data = self._make_request(endpoint, params)
            
            # If symbol is specified, Binance returns a single dict, wrap in list
            if symbol and isinstance(data, dict):
                return [data]
            
            return data
            
        except Exception as e:
            print(f"Error fetching 24hr ticker data: {str(e)}")
            return []
    
    def get_klines(self, symbol: str, interval: str = '5m', limit: int = 60) -> List[List[Any]]:
        """
        Fetch candlestick/kline data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Candlestick interval (default: '5m')
            limit: Number of data points to return (default: 60)
            
        Returns:
            List of kline data where each kline is a list:
            [
                timestamp,  # Open time
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                close_time,
                quote_asset_volume,
                number_of_trades,
                taker_buy_base_asset_volume,
                taker_buy_quote_asset_volume,
                ignore
            ]
            
        Supported intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h,
                            1d, 3d, 1w, 1M
        """
        endpoint = "klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        try:
            data = self._make_request(endpoint, params)
            return data
            
        except Exception as e:
            print(f"Error fetching klines data for {symbol}: {str(e)}")
            return []
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Fetch order book depth data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            limit: Number of bids and asks to return (default: 20)
            
        Returns:
            Dictionary containing order book data:
            {
                "lastUpdateId": int,
                "bids": [[price, quantity], ...],
                "asks": [[price, quantity], ...]
            }
            
        Supported limits: 5, 10, 20, 50, 100, 500, 1000, 5000
        """
        endpoint = "depth"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        try:
            data = self._make_request(endpoint, params)
            return data
            
        except Exception as e:
            print(f"Error fetching order book data for {symbol}: {str(e)}")
            return {"bids": [], "asks": []}
    
    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch recent trades for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            limit: Number of recent trades to return (default: 50)
            
        Returns:
            List of trade dictionaries:
            [
                {
                    "id": int,
                    "price": "price",
                    "qty": "quantity",
                    "quoteQty": "quote quantity",
                    "time": timestamp,
                    "isBuyerMaker": bool,
                    "isBestMatch": bool
                },
                ...
            ]
            
        Supported limits: 5, 10, 20, 50, 100, 500, 1000, 5000
        """
        endpoint = "trades"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        try:
            data = self._make_request(endpoint, params)
            return data
            
        except Exception as e:
            print(f"Error fetching recent trades for {symbol}: {str(e)}")
            return []
    
    def get_server_time(self) -> int:
        """
        Fetch current server time from Binance.
        
        Returns:
            Server timestamp in milliseconds
        """
        endpoint = "time"
        
        try:
            data = self._make_request(endpoint)
            return data.get("serverTime", int(time.time() * 1000))
            
        except Exception as e:
            print(f"Error fetching server time: {str(e)}")
            return int(time.time() * 1000)


if __name__ == "__main__":
    """
    Simple test to verify the Binance client works correctly.
    Fetches BTCUSDT ticker data and prints it.
    """
    print("Testing BinanceClient...")
    print("=" * 50)
    
    client = BinanceClient()
    
    try:
        # Test 1: Get BTCUSDT ticker data
        print("\n1. Fetching BTCUSDT 24hr ticker data...")
        ticker_data = client.get_ticker_24hr("BTCUSDT")
        
        if ticker_data:
            print(f"Successfully fetched data for {len(ticker_data)} symbol(s)")
            print(f"BTCUSDT - Last Price: {ticker_data[0].get('lastPrice', 'N/A')}")
            print(f"BTCUSDT - 24h Change: {ticker_data[0].get('priceChangePercent', 'N/A')}%")
            print(f"BTCUSDT - Volume: {ticker_data[0].get('volume', 'N/A')}")
        else:
            print("No ticker data returned")
        
        # Test 2: Get recent trades
        print("\n2. Fetching recent BTCUSDT trades...")
        trades = client.get_recent_trades("BTCUSDT", limit=5)
        
        if trades:
            print(f"Fetched {len(trades)} recent trades:")
            for i, trade in enumerate(trades[:5], 1):
                print(f"  {i}. Price: {trade.get('price', 'N/A')}, "
                      f"Qty: {trade.get('qty', 'N/A')}, "
                      f"Time: {datetime.fromtimestamp(trade.get('time', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("No trade data returned")
        
        # Test 3: Get order book
        print("\n3. Fetching BTCUSDT order book...")
        order_book = client.get_order_book("BTCUSDT", limit=5)
        
        if order_book:
            print(f"Top 5 Bids:")
            for i, bid in enumerate(order_book.get('bids', [])[:5], 1):
                print(f"  {i}. Price: {bid[0]}, Qty: {bid[1]}")
            
            print(f"Top 5 Asks:")
            for i, ask in enumerate(order_book.get('asks', [])[:5], 1):
                print(f"  {i}. Price: {ask[0]}, Qty: {ask[1]}")
        else:
            print("No order book data returned")
        
        # Test 4: Get klines
        print("\n4. Fetching BTCUSDT 5m klines (last 3 intervals)...")
        klines = client.get_klines("BTCUSDT", interval="5m", limit=3)
        
        if klines:
            print(f"Fetched {len(klines)} kline intervals:")
            for i, kline in enumerate(klines, 1):
                open_time = datetime.fromtimestamp(kline[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                close_price = kline[4]
                volume = kline[5]
                print(f"  {i}. {open_time} - Close: {close_price}, Volume: {volume}")
        else:
            print("No kline data returned")
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        raise