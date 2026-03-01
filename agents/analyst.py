"""
Analyst Agent for MUST Market Intelligence Agent

Performs deep market analysis on flagged symbols from WatcherAgent.
"""

from typing import List, Dict, Any, Optional
from core.binance_client import BinanceClient
import time
from datetime import datetime


class AnalystAgent:
    """Agent that analyzes market data and scores trading opportunities."""
    
    def __init__(self):
        self.client = BinanceClient()
    
    def assess_market_context(self, all_ticker_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess overall market context from all ticker data.
        
        Args:
            all_ticker_data: Full list of 24hr ticker data for all USDT pairs
            
        Returns:
            Dictionary with market context metrics
        """
        try:
            # Filter for USDT pairs and get top 20 by quoteVolume
            usdt_pairs = []
            for ticker in all_ticker_data:
                symbol = ticker.get('symbol', '')
                if symbol.endswith('USDT'):
                    try:
                        quote_volume = float(ticker.get('quoteVolume', 0))
                        price_change_pct = float(ticker.get('priceChangePercent', 0))
                        usdt_pairs.append({
                            'symbol': symbol,
                            'quoteVolume': quote_volume,
                            'priceChangePercent': price_change_pct
                        })
                    except (ValueError, TypeError):
                        continue
            
            # Sort by quoteVolume and get top 20
            usdt_pairs.sort(key=lambda x: x['quoteVolume'], reverse=True)
            top_20 = usdt_pairs[:20]
            
            if not top_20:
                return {
                    'market_wide_anomaly': False,
                    'market_sentiment': 'neutral',
                    'avg_market_volume_ratio': 0
                }
            
            # Calculate market sentiment
            total_price_change = sum(item['priceChangePercent'] for item in top_20)
            avg_price_change = total_price_change / len(top_20)
            
            if avg_price_change > 0.5:
                market_sentiment = 'bullish'
            elif avg_price_change < -0.5:
                market_sentiment = 'bearish'
            else:
                market_sentiment = 'neutral'
            
            # Check for market-wide anomaly (more than 60% of top 20 showing volume spikes)
            volume_spike_threshold = 3.0
            volume_spike_count = 0
            
            for item in top_20:
                # For market context, assume we have access to volume ratios
                # In practice, this would need to be calculated similarly to WatcherAgent
                # Here we'll use a simplified approach based on quoteVolume
                if item['quoteVolume'] > 1000000:  # Arbitrary high volume threshold
                    volume_spike_count += 1
            
            market_wide_anomaly = (volume_spike_count / len(top_20)) > 0.6
            
            # Calculate average market volume ratio (simplified)
            avg_market_volume_ratio = sum(item['quoteVolume'] for item in top_20) / len(top_20)
            
            return {
                'market_wide_anomaly': market_wide_anomaly,
                'market_sentiment': market_sentiment,
                'avg_market_volume_ratio': avg_market_volume_ratio
            }
            
        except Exception as e:
            print(f"Error assessing market context: {str(e)}")
            return {
                'market_wide_anomaly': False,
                'market_sentiment': 'neutral',
                'avg_market_volume_ratio': 0
            }
    
    def analyze_liquidity(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze order book liquidity for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Dictionary with liquidity metrics
        """
        try:
            # Get order book with 10 levels
            order_book = self.client.get_order_book(symbol, limit=10)
            
            if not order_book:
                return {
                    'bid_depth': 0,
                    'ask_depth': 0,
                    'spread_pct': 0,
                    'liquidity_score': 0
                }
            
            # Calculate bid depth (total value of top 10 bids)
            bid_depth = 0
            for bid in order_book.get('bids', [])[:10]:
                try:
                    price = float(bid[0])
                    quantity = float(bid[1])
                    bid_depth += price * quantity
                except (ValueError, TypeError, IndexError):
                    continue
            
            # Calculate ask depth (total value of top 10 asks)
            ask_depth = 0
            for ask in order_book.get('asks', [])[:10]:
                try:
                    price = float(ask[0])
                    quantity = float(ask[1])
                    ask_depth += price * quantity
                except (ValueError, TypeError, IndexError):
                    continue
            
            # Calculate spread percentage
            best_bid = float(order_book.get('bids', [[0, 0]])[0][0])
            best_ask = float(order_book.get('asks', [[0, 0]])[0][0])
            
            if best_ask > best_bid and best_bid > 0:
                spread_pct = ((best_ask - best_bid) / best_bid) * 100
            else:
                spread_pct = 0
            
            # Calculate liquidity score
            if bid_depth > 500000:
                liquidity_score = 90 + min((bid_depth - 500000) / 100000, 10)
            elif bid_depth > 100000:
                liquidity_score = 50 + ((bid_depth - 100000) / 100000) * 29
            elif bid_depth > 10000:
                liquidity_score = 20 + ((bid_depth - 10000) / 90000) * 29
            else:
                liquidity_score = (bid_depth / 10000) * 20
            
            liquidity_score = min(max(liquidity_score, 0), 100)
            
            return {
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'spread_pct': spread_pct,
                'liquidity_score': liquidity_score
            }
            
        except Exception as e:
            print(f"Error analyzing liquidity for {symbol}: {str(e)}")
            return {
                'bid_depth': 0,
                'ask_depth': 0,
                'spread_pct': 0,
                'liquidity_score': 0
            }
    
    def analyze_volume_authenticity(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze trade volume authenticity to detect potential wash trading.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Dictionary with authenticity metrics
        """
        try:
            # Get recent trades
            trades = self.client.get_recent_trades(symbol, limit=100)
            
            if not trades:
                return {
                    'unique_trade_sizes': 0,
                    'avg_trade_size': 0,
                    'authenticity_score': 0
                }
            
            # Extract unique trade quantities
            trade_quantities = set()
            total_quantity = 0
            
            for trade in trades:
                try:
                    quantity = float(trade.get('qty', 0))
                    if quantity > 0:
                        trade_quantities.add(quantity)
                        total_quantity += quantity
                except (ValueError, TypeError):
                    continue
            
            unique_trade_sizes = len(trade_quantities)
            avg_trade_size = total_quantity / len(trades) if trades else 0
            
            # Calculate authenticity score
            if unique_trade_sizes > 30:
                authenticity_score = 80 + min((unique_trade_sizes - 30) / 10, 20)
            elif unique_trade_sizes > 15:
                authenticity_score = 50 + ((unique_trade_sizes - 15) / 15) * 29
            elif unique_trade_sizes > 5:
                authenticity_score = 20 + ((unique_trade_sizes - 5) / 10) * 29
            else:
                authenticity_score = (unique_trade_sizes / 5) * 20
            
            authenticity_score = min(max(authenticity_score, 0), 100)
            
            return {
                'unique_trade_sizes': unique_trade_sizes,
                'avg_trade_size': avg_trade_size,
                'authenticity_score': authenticity_score
            }
            
        except Exception as e:
            print(f"Error analyzing volume authenticity for {symbol}: {str(e)}")
            return {
                'unique_trade_sizes': 0,
                'avg_trade_size': 0,
                'authenticity_score': 0
            }
    
    def score_opportunity(self, flagged_symbol_dict: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single flagged symbol opportunity.
        
        Args:
            flagged_symbol_dict: Dictionary from WatcherAgent with anomaly data
            market_context: Dictionary from assess_market_context()
            
        Returns:
            Comprehensive scoring dictionary
        """
        try:
            # Debug: Print incoming dict structure if needed
            if 'symbol' not in flagged_symbol_dict:
                print(f"DEBUG: Incoming dict keys: {list(flagged_symbol_dict.keys())}")
                print(f"DEBUG: Incoming dict: {flagged_symbol_dict}")
            
            symbol = flagged_symbol_dict['symbol']
            
            # Get additional analysis data
            liquidity_data = self.analyze_liquidity(symbol)
            authenticity_data = self.analyze_volume_authenticity(symbol)
            
            # Extract ratios from flagged data - using correct keys from WatcherAgent
            volume_ratio = flagged_symbol_dict.get('volume_ratio', 0)
            price_change_ratio = flagged_symbol_dict.get('price_change_ratio', 0)
            current_price = flagged_symbol_dict.get('current_price', 0)
            
            # Calculate momentum score (0-100)
            if price_change_ratio > 5:
                momentum_score = 90 + min((price_change_ratio - 5) * 2, 10)
            elif price_change_ratio > 3:
                momentum_score = 70 + ((price_change_ratio - 3) / 2) * 19
            elif price_change_ratio > 1.5:
                momentum_score = 40 + ((price_change_ratio - 1.5) / 1.5) * 29
            else:
                momentum_score = (price_change_ratio / 1.5) * 40
            
            momentum_score = min(max(momentum_score, 0), 100)
            
            # Calculate volume score (0-100)
            if volume_ratio > 5:
                volume_score = 90 + min((volume_ratio - 5) * 2, 10)
            elif volume_ratio > 3:
                volume_score = 70 + ((volume_ratio - 3) / 2) * 19
            elif volume_ratio > 1.5:
                volume_score = 40 + ((volume_ratio - 1.5) / 1.5) * 29
            else:
                volume_score = (volume_ratio / 1.5) * 40
            
            volume_score = min(max(volume_score, 0), 100)
            
            # Get scores from analysis
            liquidity_score = liquidity_data['liquidity_score']
            authenticity_score = authenticity_data['authenticity_score']
            
            # Calculate final score with market context penalty
            final_score = (
                momentum_score * 0.30 +
                volume_score * 0.25 +
                liquidity_score * 0.25 +
                authenticity_score * 0.20
            )
            
            # Apply market context penalty
            if market_context.get('market_wide_anomaly', False):
                final_score = max(final_score - 20, 0)
            
            # Determine priority level
            if final_score >= 70:
                priority_level = 'HIGH'
            elif final_score >= 45:
                priority_level = 'MONITOR'
            else:
                priority_level = 'IGNORE'
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'momentum_score': momentum_score,
                'volume_score': volume_score,
                'liquidity_score': liquidity_score,
                'authenticity_score': authenticity_score,
                'market_context_penalty': market_context.get('market_wide_anomaly', False),
                'final_score': final_score,
                'priority_level': priority_level,
                'analysis_details': {
                    'liquidity': liquidity_data,
                    'authenticity': authenticity_data
                }
            }
            
        except Exception as e:
            print(f"Error scoring opportunity for {flagged_symbol_dict.get('symbol', 'unknown')}: {str(e)}")
            return {
                'symbol': flagged_symbol_dict.get('symbol', 'unknown'),
                'current_price': 0,
                'momentum_score': 0,
                'volume_score': 0,
                'liquidity_score': 0,
                'authenticity_score': 0,
                'market_context_penalty': False,
                'final_score': 0,
                'priority_level': 'IGNORE',
                'analysis_details': {}
            }
    
    def analyze_batch(self, flagged_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze a batch of flagged symbols and return sorted results.
        
        Args:
            flagged_symbols: List of flagged symbol dictionaries from WatcherAgent
            
        Returns:
            List of scored opportunities sorted by final_score descending
        """
        try:
            # Get market context once
            all_ticker_data = self.client.get_ticker_24hr()
            market_context = self.assess_market_context(all_ticker_data)
            
            # Score each flagged symbol
            scored_results = []
            for flagged in flagged_symbols:
                scored = self.score_opportunity(flagged, market_context)
                scored_results.append(scored)
            
            # Sort by final_score descending
            scored_results.sort(key=lambda x: x['final_score'], reverse=True)
            return scored_results
            
        except Exception as e:
            print(f"Error analyzing batch: {str(e)}")
            return []


if __name__ == "__main__":
    """
    Test the AnalystAgent by analyzing flagged symbols.
    """
    print("Testing AnalystAgent...")
    print("=" * 50)
    
    try:
        # Create WatcherAgent to get flagged symbols
        from agents.watcher import WatcherAgent
        
        watcher = WatcherAgent()
        flagged_symbols = watcher.scan_for_anomalies()
        
        if flagged_symbols:
            print(f"\nFound {len(flagged_symbols)} symbol(s) with anomalies")
            print("Analyzing opportunities...")
            
            analyst = AnalystAgent()
            results = analyst.analyze_batch(flagged_symbols)
            
            if results:
                print(f"\nTop 5 Trading Opportunities:")
                for i, result in enumerate(results[:5], 1):
                    print(f"\n{i}. {result['symbol']}")
                    print(f"   Final Score: {result['final_score']:.1f} ({result['priority_level']})")
                    print(f"   Momentum: {result['momentum_score']:.0f}, Volume: {result['volume_score']:.0f}")
                    print(f"   Liquidity: {result['liquidity_score']:.0f}, Authenticity: {result['authenticity_score']:.0f}")
                    print(f"   Market Context Penalty: {result['market_context_penalty']})")
            else:
                print("No opportunities found")
        else:
            print("No anomalies detected by WatcherAgent")
        
        print("\n" + "=" * 50)
        print("AnalystAgent test completed!")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        raise