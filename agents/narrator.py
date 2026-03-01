"""
Narrator Agent for MUST Market Intelligence Agent

Generates plain-English situation reports using Groq API.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    raise ImportError("groq library not installed. Run: pip install groq")

# Load environment variables from .env file
load_dotenv()


class NarratorAgent:
    """Agent that generates plain-English situation reports from analysis results."""
    
    def __init__(self):
        """Initialize Groq client with API key."""
        try:
            # Get API key from environment
            groq_api_key = os.getenv('GROQ_API_KEY')
            
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            # Initialize Groq client
            self.client = Groq(api_key=groq_api_key)
            
            # Set model
            self.model = 'llama-3.3-70b-versatile'
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Groq API: {str(e)}")
    
    def generate_report(self, analyst_result: Dict[str, Any]) -> str:
        """
        Generate a plain-English report for a single analysis result.
        
        Args:
            analyst_result: Dictionary from AnalystAgent output
            
        Returns:
            Plain-English report string
        """
        try:
            # Extract and round data from analyst result
            symbol = analyst_result['symbol']
            current_price = round(analyst_result.get('current_price', 0), 2)
            priority_level = analyst_result['priority_level']
            final_score = round(analyst_result.get('final_score', 0), 1)
            momentum_score = round(analyst_result.get('momentum_score', 0), 1)
            volume_score = round(analyst_result.get('volume_score', 0), 1)
            liquidity_score = round(analyst_result.get('liquidity_score', 0), 1)
            authenticity_score = round(analyst_result.get('authenticity_score', 0), 1)
            
            # Get market context from analysis details
            market_context = analyst_result.get('analysis_details', {})
            market_sentiment = market_context.get('market_sentiment', 'neutral')
            market_wide_anomaly = market_context.get('market_wide_anomaly', False)
            
            # Create structured prompt for Groq
            prompt = f"""You are a sharp market intelligence analyst. Your job is to turn raw market data into clear, specific, actionable intelligence for a busy trader or fintech business owner who does NOT stare at charts all day.

Here is the market data:
- Symbol: {symbol}
- Current Price: ${current_price}
- Priority Level: {priority_level}
- Overall Score: {final_score}/100
- Momentum Score: {momentum_score}/100 (how fast and strongly price is moving)
- Volume Score: {volume_score}/100 (how unusual the trading volume is)
- Liquidity Score: {liquidity_score}/100 (how easy it would be to exit a position)
- Authenticity Score: {authenticity_score}/100 (how genuine the volume looks vs wash trading)
- Market Sentiment: {market_sentiment}
- Market-Wide Event: {market_wide_anomaly}

Write EXACTLY 3 sentences. Be specific. Use the actual numbers and scores to justify what you say.

Sentence 1: Describe what is specifically happening with this asset RIGHT NOW. Mention the actual price and what the scores reveal. Example style: 'SOL is showing a volume spike 8x its normal level at $87, but liquidity is deep enough to support real trading.'

Sentence 2: Explain what this specifically means for someone making a decision today — mention whether this looks like a genuine opportunity or a potential trap based on the liquidity and authenticity scores.

Sentence 3: Start with {priority_level}: then give one direct, specific recommendation based on all the data.

Hard rules:
- Never say 'stable' or 'normal' or 'trading normally' — if it scored high enough to be analyzed, something is happening
- Never use jargon like RSI, MACD, Bollinger bands
- Never be vague — every sentence must reference specific data points
- Maximum 90 words total
- No bullet points, just 3 clean sentences

Additional formatting rules:
- Never print raw score numbers in sentences. Instead translate them to plain English:
  * Score 80-100 = 'strong' or 'high'
  * Score 50-79 = 'moderate'  
  * Score 20-49 = 'weak' or 'thin'
  * Score 0-19 = 'very low' or 'concerning'
- For liquidity specifically: high liquidity = 'easy to exit', low liquidity = 'hard to exit safely'
- For authenticity: high = 'looks like genuine trading activity', low = 'shows signs of artificial volume'
- Vary your language — do not use 'buy with caution' more than once across all reports
- Write like a human analyst talking to a colleague, not a robot reading a spreadsheet
"""
            
            # Generate report using Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a market intelligence analyst writing for a non-technical business executive or retail trader."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            
            # Return the generated content
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating report for {symbol}: {str(e)}")
            return f"Unable to generate report for {symbol} due to API error. Please check your Groq API key and try again."
    
    def generate_batch_reports(self, analyst_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate reports for a batch of analysis results.
        
        Args:
            analyst_results: List of dictionaries from AnalystAgent output
            
        Returns:
            List of dictionaries with added 'report' key
        """
        try:
            results_with_reports = []
            
            for result in analyst_results:
                report = self.generate_report(result)
                result_with_report = result.copy()
                result_with_report['report'] = report
                results_with_reports.append(result_with_report)
            
            return results_with_reports
            
        except Exception as e:
            print(f"Error generating batch reports: {str(e)}")
            return []
    
    def format_final_output(self, reports: List[Dict[str, Any]]) -> None:
        """
        Format and print the final situation report to console.
        
        Args:
            reports: List of dictionaries with analysis results and reports
        """
        try:
            # Get current timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Print header
            print(f"\n{'='*60}")
            print(f"MUST MARKET INTELLIGENCE — {timestamp}")
            print(f"{'='*60}")
            
            # Print each report
            for report in reports:
                symbol = report['symbol']
                priority_level = report['priority_level']
                final_score = report['final_score']
                report_text = report['report']
                
                # Determine emoji based on priority
                if priority_level == 'HIGH':
                    emoji = '🔴'
                elif priority_level == 'MONITOR':
                    emoji = '🟡'
                else:
                    emoji = '⚪'
                
                # Print formatted report
                print(f"\n{emoji} {priority_level} — {symbol} — Score: {final_score:.1f}/100")
                print(report_text)
            
            # Print footer
            print(f"\n{'='*60}")
            print("Situation report completed.")
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"Error formatting final output: {str(e)}")
            raise


if __name__ == "__main__":
    """
    Test the NarratorAgent with mock data.
    """
    print("Testing NarratorAgent...")
    print("=" * 50)
    
    try:
        # Import required modules
        from agents.analyst import AnalystAgent
        
        # Create mock data (same as test_pipeline.py)
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
        
        # Run analysis
        print("\nStep 1: Running AnalystAgent...")
        analyst = AnalystAgent()
        results = analyst.analyze_batch(mock_flagged)
        
        if not results:
            print("Analysis failed — no results generated")
            sys.exit(1)
        
        # Generate reports
        print("\nStep 2: Generating reports with NarratorAgent...")
        narrator = NarratorAgent()
        reports = narrator.generate_batch_reports(results)
        
        # Format and display final output
        print("\nStep 3: Displaying situation report...")
        narrator.format_final_output(reports)
        
        print("\n" + "=" * 50)
        print("NarratorAgent test completed!")
        
    except ImportError as e:
        print(f"\nImport error: {str(e)}")
        print("Please install required dependencies:")
        print("pip install groq python-dotenv")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        raise
