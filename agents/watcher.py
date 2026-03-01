"""
Watcher Agent for MUST Market Intelligence Agent

Monitors Binance market data and flags anomalies based on volume and price movements.
"""

from typing import List, Dict, Optional, Any
from core.binance_client import BinanceClient
import time
from datetime import datetime
import yaml
import os


class WatcherAgent:
    """Agent that monitors Binance market data and detects anomalies."""
    
    def __init__(self):
        self.client = BinanceClient()
        self.thresholds = self._load_thresholds()
    
    def get_top_symbols(self, n: int = 20) -> List[str]:
        """
        Get top trading symbols by 24hr quote volume.
        
        Args:
            n: Number of top symbols to return
            
        Returns:
            List of top n symbols (USDT pairs only) sorted by quoteVolume descending
        """
        try:
            # Fetch all 24hr ticker data
            ticker_data = self.client.get_ticker_24hr()
            
            if not ticker_data:
                print("No ticker data available")
                return []
            
            # Filter for USDT pairs and extract quoteVolume
            usdt_pairs = []
            for ticker in ticker_data:
                symbol = ticker.get('symbol', '')
                if symbol.endswith('USDT'):
                    try:
                        quote_volume = float(ticker.get('quoteVolume', 0))
                        usdt_pairs.append({
                            'symbol': symbol,
                            'quoteVolume': quote_volume
                        })
                    except (ValueError, TypeError):
                        continue
            
            # Sort by quoteVolume descending and return top n symbols
            usdt_pairs.sort(key=lambda x: x['quoteVolume'], reverse=True)
            return [pair['symbol'] for pair in usdt_pairs[:n]]
            
        except Exception as e:
            print(f"Error fetching top symbols: {str(e)}")
            return []
    
    def get_symbol_baseline(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate baseline metrics for a symbol using historical kline data.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Dictionary with avg_volume, avg_price_change_pct, and current_price
        """
        try:
            # Get last 60 five-minute klines
            klines = self.client.get_klines(symbol, interval='5m', limit=60)
            
            if not klines or len(klines) < 2:
                print(f"Insufficient kline data for {symbol}")
                return {}
            
            # Calculate average volume and average price change percentage
            total_volume = 0
            total_price_change_pct = 0
            
            for kline in klines[:-1]:  # Exclude most recent incomplete candle
                try:
                    volume = float(kline[5])
                    open_price = float(kline[1])
                    close_price = float(kline[4])
                    
                    if open_price > 0:
                        price_change_pct = abs((close_price - open_price) / open_price) * 100
                        total_volume += volume
                        total_price_change_pct += price_change_pct
                except (ValueError, TypeError, IndexError):
                    continue
            
            avg_volume = total_volume / (len(klines) - 1) if len(klines) > 1 else 0
            avg_price_change_pct = total_price_change_pct / (len(klines) - 1) if len(klines) > 1 else 0
            
            # Get current price from most recent complete candle
            current_price = float(klines[-1][4]) if len(klines) > 0 else 0
            
            return {
                'symbol': symbol,
                'avg_volume': avg_volume,
                'avg_price_change_pct': avg_price_change_pct,
                'current_price': current_price
            }
            
        except Exception as e:
            print(f"Error calculating baseline for {symbol}: {str(e)}")
            return {}
    
    def _load_thresholds(self) -> Dict[str, float]:
        """
        Load anomaly thresholds from config.yaml with default values.
        
        Returns:
            Dictionary with volume_ratio and price_change_ratio thresholds
        """
        config_path = 'config.yaml'
        default_thresholds = {
            'volume_ratio': 2.0,
            'price_change_ratio': 1.8
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    config = yaml.safe_load(file)
                    
                if config and 'anomaly_thresholds' in config:
                    return {
                        'volume_ratio': config['anomaly_thresholds'].get('volume_ratio', default_thresholds['volume_ratio']),
                        'price_change_ratio': config['anomaly_thresholds'].get('price_change_ratio', default_thresholds['price_change_ratio'])
                    }
        
        except Exception as e:
            print(f"Error loading thresholds from config: {str(e)}")
            print("Using default threshold values")
        
        return default_thresholds
    
    def scan_for_anomalies(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Scan symbols for volume and price anomalies.
        
        Args:
            symbols: List of symbols to scan. If None, uses top 20 USDT pairs.
            
        Returns:
            List of flagged symbols with anomaly details
        """
        try:
            # Get symbols to scan
            if symbols is None:
                symbols = self.get_top_symbols(20)
            
            if not symbols:
                print("No symbols to scan")
                return []
            
            flagged_symbols = []
            
            for symbol in symbols:
                # Get baseline metrics
                baseline = self.get_symbol_baseline(symbol)
                
                if not baseline or baseline['avg_volume'] == 0:
                    continue
                
                # Get most recent single kline (last 5 minutes)
                recent_klines = self.client.get_klines(symbol, interval='5m', limit=1)
                
                if not recent_klines or len(recent_klines) < 1:
                    continue
                
                try:
                    # Extract current candle data
                    current_kline = recent_klines[0]
                    current_volume = float(current_kline[5])
                    current_open = float(current_kline[1])
                    current_close = float(current_kline[4])
                    
                    if current_open > 0:
                        current_price_change_pct = abs((current_close - current_open) / current_open) * 100
                    else:
                        continue
                    
                    # Calculate ratios
                    volume_ratio = current_volume / baseline['avg_volume']
                    price_change_ratio = current_price_change_pct / baseline['avg_price_change_pct'] if baseline['avg_price_change_pct'] > 0 else 0
                    
                    # Check anomaly conditions
                    volume_spike = volume_ratio > self.thresholds['volume_ratio']
                    price_spike = price_change_ratio > self.thresholds['price_change_ratio']
                    
                    if volume_spike or price_spike:
                        reason = []
                        if volume_spike and price_spike:
                            reason = 'both'
                        elif volume_spike:
                            reason = 'volume_spike'
                        else:
                            reason = 'price_spike'
                        
                        flagged_symbols.append({
                            'symbol': symbol,
                            'current_price': current_close,
                            'volume_ratio': volume_ratio,
                            'price_change_ratio': price_change_ratio,
                            'reason': reason
                        })
                        
                except (ValueError, TypeError, IndexError):
                    continue
            
            return flagged_symbols
            
        except Exception as e:
            print(f"Error scanning for anomalies: {str(e)}")
            return []


if __name__ == "__main__":
    """
    Test the WatcherAgent by scanning for anomalies.
    """
    print("Testing WatcherAgent...")
    print("=" * 50)
    
    watcher = WatcherAgent()
    
    try:
        # Scan for anomalies
        print("\nScanning for market anomalies...")
        flagged = watcher.scan_for_anomalies()
        
        if flagged:
            print(f"Found {len(flagged)} symbol(s) with anomalies:")
            for item in flagged:
                print(f"\nSymbol: {item['symbol']}")
                print(f"  Current Price: ${item['current_price']:.2f}")
                print(f"  Volume Ratio: {item['volume_ratio']:.2f}x")
                print(f"  Price Change Ratio: {item['price_change_ratio']:.2f}x")
                print(f"  Reason: {item['reason']}")
        else:
            print("No anomalies detected")
        
        print("\n" + "=" * 50)
        print("WatcherAgent test completed!")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        raise