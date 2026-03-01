"""
PerformanceScorer for MUST Market Intelligence Agent

Calculates comprehensive performance scores for the analysis pipeline.
"""

import os
import sys
import json
import time
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to PYTHONPATH to enable imports from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PerformanceScorer:
    """Class that implements the 1-10,000 scoring system for quest submissions."""
    
    def __init__(self):
        """Initialize the PerformanceScorer."""
        self.max_score = 10000
        self.dimension_weights = {
            'signal_accuracy': 0.40,  # 4000 points
            'narration_quality': 0.35,  # 3500 points
            'pipeline_speed': 0.15,  # 1500 points
            'coverage': 0.10   # 1000 points
        }
    
    def calculate_score(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate the final score out of 10,000 with full breakdown.
        
        Args:
            test_results: List of past analysis results from JSON reports
            
        Returns:
            Dictionary with final score and detailed breakdown
        """
        try:
            # Handle empty results
            if not test_results:
                return self._create_empty_score()
            
            # Calculate each dimension
            signal_accuracy = self._calculate_signal_accuracy(test_results)
            narration_quality = self._calculate_narration_quality(test_results)
            pipeline_speed = self._calculate_pipeline_speed()
            coverage = self._calculate_coverage(test_results)
            
            # Calculate final score
            final_score = (
                signal_accuracy['points'] + 
                narration_quality['points'] + 
                pipeline_speed['points'] + 
                coverage['points']
            )
            
            # Create breakdown
            breakdown = {
                'signal_accuracy': signal_accuracy,
                'narration_quality': narration_quality,
                'pipeline_speed': pipeline_speed,
                'coverage': coverage
            }
            
            return {
                'final_score': final_score,
                'max_score': self.max_score,
                'breakdown': breakdown,
                'calculation_method': 'Weighted formula: Signal Accuracy 40% + Narration Quality 35% + Pipeline Speed 15% + Coverage 10%'
            }
            
        except Exception as e:
            print(f"Error calculating score: {str(e)}")
            return self._create_empty_score()
    
    def _calculate_signal_accuracy(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate signal accuracy dimension (4000 points max)."""
        try:
            # Check if test_scenarios directory exists
            scenarios_dir = Path('tests/test_scenarios')
            use_scenarios = scenarios_dir.exists() and list(scenarios_dir.rglob('*.json'))
            
            # If scenarios exist, use them; otherwise use current test results
            if use_scenarios:
                # Load scenarios (simplified - in practice would load actual scenario files)
                # For now, we'll use the test_results as scenarios
                results_to_use = test_results
            else:
                results_to_use = test_results
            
            # Count meaningful signals
            meaningful_signals = 0
            total_results = len(results_to_use)
            
            for result in results_to_use:
                priority_level = result.get('priority_level', 'IGNORE')
                final_score = result.get('final_score', 0)
                
                if priority_level != 'IGNORE' and final_score > 35:
                    meaningful_signals += 1
            
            # Calculate points
            if total_results > 0:
                accuracy_pct = (meaningful_signals / total_results) * 100
                points = (meaningful_signals / total_results) * 4000
            else:
                accuracy_pct = 0
                points = 0
            
            return {
                'points': round(points, 2),
                'max': 4000,
                'pct': round(accuracy_pct, 2)
            }
            
        except Exception as e:
            print(f"Error calculating signal accuracy: {str(e)}")
            return {'points': 0, 'max': 4000, 'pct': 0}
    
    def _calculate_narration_quality(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate narration quality dimension (3500 points max)."""
        try:
            total_points = 0
            max_possible_points = 0
            jargon_words = {'RSI', 'MACD', 'Bollinger', 'SMA', 'EMA', 'Fibonacci', 'pivot', 'resistance', 'support'}
            
            for result in test_results:
                report = result.get('report', '')
                
                if report:
                    # Calculate points for this report
                    report_points = 0
                    
                    # Length between 40-90 words: +1 point
                    word_count = len(report.split())
                    if 40 <= word_count <= 90:
                        report_points += 1
                    
                    # Contains priority level word: +1 point
                    priority_level = result.get('priority_level', '').upper()
                    if priority_level in ['HIGH', 'MONITOR', 'IGNORE']:
                        if priority_level in report.upper():
                            report_points += 1
                    
                    # Does not contain jargon words: +1 point
                    contains_jargon = any(jargon_word.upper() in report.upper() for jargon_word in jargon_words)
                    if not contains_jargon:
                        report_points += 1
                    
                    # Contains price reference ($ symbol): +1 point
                    if '$' in report:
                        report_points += 1
                    
                    total_points += report_points
                    max_possible_points += 4
            
            # Calculate final points
            if max_possible_points > 0:
                quality_pct = (total_points / max_possible_points) * 100
                points = (total_points / max_possible_points) * 3500
            else:
                quality_pct = 0
                points = 0
            
            return {
                'points': round(points, 2),
                'max': 3500,
                'pct': round(quality_pct, 2)
            }
            
        except Exception as e:
            print(f"Error calculating narration quality: {str(e)}")
            return {'points': 0, 'max': 3500, 'pct': 0}
    
    def _calculate_pipeline_speed(self) -> Dict[str, Any]:
        """Calculate pipeline speed dimension (1500 points max)."""
        try:
            # Import orchestrator locally to avoid circular imports
            from core.orchestrator import Orchestrator
            
            # Time the run_once() method
            start_time = time.time()
            orchestrator = Orchestrator()
            results = orchestrator.run_once()
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Calculate points based on time
            if execution_time < 10:
                points = 1500
            elif execution_time < 20:
                points = 1000
            elif execution_time < 30:
                points = 500
            else:
                points = 200
            
            speed_pct = (points / 1500) * 100 if points > 0 else 0
            
            return {
                'points': round(points, 2),
                'max': 1500,
                'pct': round(speed_pct, 2),
                'execution_time': round(execution_time, 2)
            }
            
        except Exception as e:
            print(f"Error calculating pipeline speed: {str(e)}")
            return {'points': 0, 'max': 1500, 'pct': 0, 'execution_time': 0}
    
    def _calculate_coverage(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate coverage dimension (1000 points max)."""
        try:
            complete_results = 0
            total_results = len(test_results)
            
            for result in test_results:
                # Check if all four component scores are present
                if all(key in result for key in ['momentum_score', 'volume_score', 'liquidity_score', 'authenticity_score']):
                    complete_results += 1
            
            # Calculate points
            if total_results > 0:
                coverage_pct = (complete_results / total_results) * 100
                points = (complete_results / total_results) * 1000
            else:
                coverage_pct = 0
                points = 0
            
            return {
                'points': round(points, 2),
                'max': 1000,
                'pct': round(coverage_pct, 2)
            }
            
        except Exception as e:
            print(f"Error calculating coverage: {str(e)}")
            return {'points': 0, 'max': 1000, 'pct': 0}
    
    def _create_empty_score(self) -> Dict[str, Any]:
        """Create a score dictionary with all zeros."""
        return {
            'final_score': 0,
            'max_score': self.max_score,
            'breakdown': {
                'signal_accuracy': {'points': 0, 'max': 4000, 'pct': 0},
                'narration_quality': {'points': 0, 'max': 3500, 'pct': 0},
                'pipeline_speed': {'points': 0, 'max': 1500, 'pct': 0},
                'coverage': {'points': 0, 'max': 1000, 'pct': 0}
            },
            'calculation_method': 'Weighted formula: Signal Accuracy 40% + Narration Quality 35% + Pipeline Speed 15% + Coverage 10%'
        }
    
    def print_score_report(self, score_dict: Dict[str, Any]) -> None:
        """
        Print a clean formatted score report.
        
        Args:
            score_dict: Dictionary from calculate_score() method
        """
        try:
            # Get breakdown data
            breakdown = score_dict.get('breakdown', {})
            
            # Print formatted report
            print("\n" + "="*60)
            print("     MUST Agent Performance Score        ")
            print("="*60)
            
            # Print each dimension
            for dimension, data in breakdown.items():
                points = data.get('points', 0)
                max_points = data.get('max', 0)
                pct = data.get('pct', 0)
                
                # Format the line
                line = f"║  {dimension.replace('_', ' ').title()}:   {points:5.0f} / {max_points:4d}  ({pct:3.0f}%)  ║"
                print(line)
            
            # Print separator
            print("="*60)
            
            # Print final score
            final_score = score_dict.get('final_score', 0)
            final_pct = (final_score / self.max_score) * 100
            final_line = f"║  FINAL SCORE:       {final_score:5.0f} / {self.max_score:5d}  ({final_pct:3.0f}%) ║"
            print(final_line)
            
            # Print bottom border
            print("="*60)
            
        except Exception as e:
            print(f"Error printing score report: {str(e)}")


if __name__ == "__main__":
    """
    Test the PerformanceScorer.
    
    This test:
    1. Loads the most recent JSON report from output/reports/ directory
    2. Runs calculate_score() on it
    3. Calls print_score_report()
    4. Times a live run_once() call from Orchestrator for the speed dimension
    5. Handles the case where no reports exist yet by using mock data
    """
    print("Testing PerformanceScorer...")
    print("=" * 50)
    
    try:
        # Create PerformanceScorer instance
        scorer = PerformanceScorer()
        
        # Try to load the most recent report
        reports_dir = Path('output/reports')
        test_results = []
        
        if reports_dir.exists():
            # Find all JSON files and get the most recent one
            json_files = list(reports_dir.rglob('*.json'))
            
            if json_files:
                # Sort by modification time and get the most recent
                json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                most_recent_file = json_files[0]
                
                print(f"Loading most recent report: {most_recent_file.name}")
                
                # Load the JSON data
                with open(most_recent_file, 'r') as f:
                    test_results = json.load(f)
            else:
                print("No JSON reports found in output/reports/")
        else:
            print("output/reports/ directory does not exist")
        
        # If no results loaded, use mock data
        if not test_results:
            print("Using mock data for testing...")
            test_results = [
                {
                    "symbol": "BTCUSDT",
                    "current_price": 67000.0,
                    "momentum_score": 85,
                    "volume_score": 90,
                    "liquidity_score": 75,
                    "authenticity_score": 80,
                    "final_score": 82.5,
                    "priority_level": "HIGH",
                    "report": "BTC is showing strong momentum with volume 4.5x normal at $67,000. The liquidity is deep enough to support real trading activity. This looks like a genuine opportunity based on the high authenticity score. HIGH: Consider entering a position with proper risk management."
                },
                {
                    "symbol": "ETHUSDT",
                    "current_price": 2050.0,
                    "momentum_score": 70,
                    "volume_score": 65,
                    "liquidity_score": 85,
                    "authenticity_score": 70,
                    "final_score": 67.5,
                    "priority_level": "MONITOR",
                    "report": "ETH is experiencing moderate volume increase at $2,050. The liquidity is good but the momentum is not as strong. This appears to be a legitimate trading opportunity but requires monitoring. MONITOR: Watch for confirmation of trend continuation."
                },
                {
                    "symbol": "SOLUSDT",
                    "current_price": 87.0,
                    "momentum_score": 60,
                    "volume_score": 55,
                    "liquidity_score": 65,
                    "authenticity_score": 60,
                    "final_score": 55.0,
                    "priority_level": "MONITOR",
                    "report": "SOL shows average volume and momentum at $87. The liquidity and authenticity scores are moderate. This is a potential opportunity but not urgent. MONITOR: Keep an eye on volume patterns."
                }
            ]
        
        # Calculate score
        print("\nCalculating performance score...")
        score_dict = scorer.calculate_score(test_results)
        
        # Print score report
        print("\nPerformance Score Report:")
        scorer.print_score_report(score_dict)
        
        # Print additional information
        speed_data = score_dict['breakdown']['pipeline_speed']
        print(f"\nPipeline Speed: {speed_data['execution_time']:.2f} seconds")
        print(f"Total results analyzed: {len(test_results)}")
        
        print("\n" + "=" * 50)
        print("PerformanceScorer test completed!")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        raise
