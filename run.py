"""
Main entry point for MUST Market Intelligence Agent

Orchestrates the complete analysis pipeline with command line options.
"""

import sys
import os
import argparse
from datetime import datetime
from typing import Dict, Any

# Add project root to PYTHONPATH to enable imports from anywhere
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import after setting up PYTHONPATH
from core.orchestrator import Orchestrator


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description='MUST Market Intelligence Agent')
    parser.add_argument('--once', action='store_true', help='Run single analysis and exit')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring loop')
    parser.add_argument('--test', action='store_true', help='Run in test mode with mock data')
    
    args = parser.parse_args()
    
    # Print startup banner
    print("\n" + "=" * 60)
    print("   MUST Market Intelligence Agent v1.0   ")
    print("   Powered by Binance + Groq LLaMA       ")
    print("=" * 60)
    
    mode = "TEST" if args.test else "LIVE"
    print(f"\nRunning in {mode} mode")
    
    try:
        orchestrator = Orchestrator()
        
        if args.test:
            print("\nTest mode: Using mock data instead of live anomalies")
            mock_flagged = [
                {"symbol": "BTCUSDT", "current_price": 67000.0, "volume_ratio": 4.5, "price_change_ratio": 3.2, "reason": "both"},
                {"symbol": "ETHUSDT", "current_price": 2050.0, "volume_ratio": 2.1, "price_change_ratio": 5.8, "reason": "price_spike"},
                {"symbol": "SOLUSDT", "current_price": 87.0, "volume_ratio": 8.3, "price_change_ratio": 1.2, "reason": "volume_spike"}
            ]
            
            print(f"\nStep 1: Analyzing {len(mock_flagged)} mock symbol(s)...")
            results = orchestrator.run_test(mock_flagged)
            
            if not results:
                print("\nTest analysis failed — no results generated")
                print("=" * 60)
                sys.exit(1)
            
            print(f"\nStep 2: Displaying test results...")
            print(f"\nFound {len(results)} total test opportunities")
            
            # Show top 5 results
            for i, result in enumerate(results[:5], 1):
                print(format_analysis_result(result))
            
            # Show summary if more than 5 results
            if len(results) > 5:
                print(f"\n... and {len(results) - 5} more test opportunities available")
            
            print("\n" + "=" * 60)
            print("Test mode completed successfully!")
            print("=" * 60)
            
        elif args.continuous:
            print("\nStarting continuous monitoring...")
            print(f"Scan interval: {orchestrator.scan_interval} seconds")
            print("Press Ctrl+C to stop")
            print("=" * 60)
            orchestrator.run_continuous()
        else:
            print("\nRunning single analysis...")
            results = orchestrator.run_once()
            
            if results:
                print(f"\nGenerated {len(results)} analysis results")
                for i, result in enumerate(results[:3], 1):
                    print(f"  {i}. {result['symbol']} - {result['priority_level']} - Score: {result['final_score']:.1f}")
            else:
                print("No results generated")
            
            print("\n" + "=" * 60)
            print("Analysis completed!")
            print("=" * 60)
            
    except KeyboardInterrupt:
        print(f"\n\n{'='*60}")
        print("Operation cancelled by user.")
        print(f"{'='*60}")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


def format_analysis_result(result: Dict[str, Any]) -> str:
    """Format a single analysis result for display."""
    details = result.get('analysis_details', {})
    liquidity = details.get('liquidity', {})
    
    output = f"\n{'='*50}\n"
    output += f"Symbol: {result['symbol']}\n"
    output += f"Current Price: ${result['current_price']:.2f}\n"
    output += f"Priority: {result['priority_level']}\n"
    output += f"Final Score: {result['final_score']:.1f}/100\n"
    output += f"\nComponent Scores:\n"
    output += f"  Momentum: {result['momentum_score']:.0f}\n"
    output += f"  Volume: {result['volume_score']:.0f}\n"
    output += f"  Liquidity: {result['liquidity_score']:.0f}\n"
    output += f"  Authenticity: {result['authenticity_score']:.0f}\n"
    output += f"\nMarket Context:\n"
    output += f"  Market Wide Anomaly Penalty: {result['market_context_penalty']}\n"
    output += f"  Bid Depth: ${liquidity.get('bid_depth', 0):,.0f}\n"
    output += f"  Spread: {liquidity.get('spread_pct', 0):.2f}%\n"
    output += f"{'='*50}"
    return output


if __name__ == "__main__":
    main()