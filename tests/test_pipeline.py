"""
Test pipeline for MUST Market Intelligence Agent

Tests the full Watcher → Analyst pipeline using mock data and live API calls.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any
# Add project root to PYTHONPATH to enable imports from anywhere
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..'))

# Import after setting up PYTHONPATH
from agents.analyst import AnalystAgent


def print_analysis_result(result: Dict[str, Any], title: str = "Analysis Result"):
    """Print formatted analysis result."""
    details = result.get('analysis_details', {})
    liquidity = details.get('liquidity', {})
    
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Symbol: {result['symbol']}")
    print(f"Current Price: ${result['current_price']:.2f}")
    print(f"Priority: {result['priority_level']}")
    print(f"Final Score: {result['final_score']:.1f}/100")
    print(f"\nComponent Scores:")
    print(f"  Momentum: {result['momentum_score']:.0f}")
    print(f"  Volume: {result['volume_score']:.0f}")
    print(f"  Liquidity: {result['liquidity_score']:.0f}")
    print(f"  Authenticity: {result['authenticity_score']:.0f}")
    print(f"\nMarket Context:")
    print(f"  Market Wide Anomaly Penalty: {result['market_context_penalty']}")
    print(f"  Bid Depth: ${liquidity.get('bid_depth', 0):,.0f}")
    print(f"  Spread: {liquidity.get('spread_pct', 0):.2f}%")
    print(f"{'='*50}")


def print_liquidity_analysis(result: Dict[str, Any]):
    """Print formatted liquidity analysis."""
    print(f"\n{'='*50}")
    print("Liquidity Analysis")
    print(f"{'='*50}")
    print(f"Symbol: {result.get('symbol', 'N/A')}")
    print(f"Bid Depth: ${result.get('bid_depth', 0):,.0f}")
    print(f"Ask Depth: ${result.get('ask_depth', 0):,.0f}")
    print(f"Spread: {result.get('spread_pct', 0):.2f}%")
    print(f"Liquidity Score: {result.get('liquidity_score', 0):.0f}/100")
    print(f"{'='*50}")


def print_authenticity_analysis(result: Dict[str, Any]):
    """Print formatted authenticity analysis."""
    print(f"\n{'='*50}")
    print("Volume Authenticity Analysis")
    print(f"{'='*50}")
    print(f"Symbol: {result.get('symbol', 'N/A')}")
    print(f"Unique Trade Sizes: {result.get('unique_trade_sizes', 0)}")
    print(f"Average Trade Size: {result.get('avg_trade_size', 0):,.2f}")
    print(f"Authenticity Score: {result.get('authenticity_score', 0):.0f}/100")
    print(f"{'='*50}")


if __name__ == "__main__":
    """
    Test the full Watcher → Analyst pipeline with mock data and live API calls.
    """
    print("Testing MUST Market Intelligence Agent Pipeline...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Create AnalystAgent instance
        analyst = AnalystAgent()
        
        # Mock data for testing
        mock_flagged = [
            {
                "symbol": "BTCUSDT",
                "current_price": 67000.0,
                "volume_ratio": 4.5,
                "price_change_ratio": 3.2,
                "reason": "both"
            },
            {
                "symbol": "ETHUSDT", 
                "current_price": 2050.0,
                "volume_ratio": 2.1,
                "price_change_ratio": 5.8,
                "reason": "price_spike"
            },
            {
                "symbol": "SOLUSDT",
                "current_price": 87.0,
                "volume_ratio": 8.3,
                "price_change_ratio": 1.2,
                "reason": "volume_spike"
            }
        ]
        
        mock_market_context = {
            "market_wide_anomaly": False,
            "market_sentiment": "bullish",
            "avg_market_volume_ratio": 2.1
        }
        
        print("\n1. Testing score_opportunity() with mock data...")
        print("=" * 50)
        
        for i, flagged in enumerate(mock_flagged, 1):
            print(f"\nAnalyzing symbol {i}: {flagged['symbol']}")
            result = analyst.score_opportunity(flagged, mock_market_context)
            print_analysis_result(result, f"Symbol {i} Analysis")
        
        print(f"\n{'='*50}")
        print("Mock data testing completed!")
        
        # Test live API calls for BTCUSDT
        print("\n2. Testing live API calls for BTCUSDT...")
        print("=" * 50)
        
        btc_symbol = "BTCUSDT"
        
        # Test liquidity analysis
        print(f"\nTesting liquidity analysis for {btc_symbol}...")
        liquidity_result = analyst.analyze_liquidity(btc_symbol)
        liquidity_result['symbol'] = btc_symbol
        print_liquidity_analysis(liquidity_result)
        
        # Test volume authenticity analysis
        print(f"\nTesting volume authenticity analysis for {btc_symbol}...")
        authenticity_result = analyst.analyze_volume_authenticity(btc_symbol)
        authenticity_result['symbol'] = btc_symbol
        print_authenticity_analysis(authenticity_result)
        
        print(f"\n{'='*50}")
        print("Live API testing completed!")
        
        print(f"\n{'='*50}")
        print("Pipeline testing completed successfully!")
        
    except Exception as e:
        print(f"\nError running pipeline test: {str(e)}")
        raise