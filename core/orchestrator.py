"""
Orchestrator for MUST Market Intelligence Agent

Main orchestration class that runs the full pipeline autonomously.
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import yaml
from pathlib import Path

# Add project root to PYTHONPATH to enable imports from anywhere
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..'))

# Import after setting up PYTHONPATH
from agents.watcher import WatcherAgent
from agents.analyst import AnalystAgent
from agents.narrator import NarratorAgent


class Orchestrator:
    """Main orchestration class that runs the full analysis pipeline."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            # Load configuration
            self.config = self._load_config(config_path)
            
            # Initialize agents
            self.watcher = WatcherAgent()
            self.analyst = AnalystAgent()
            self.narrator = NarratorAgent()
            
            # Set configuration parameters
            self.scan_interval = self.config.get('scan_interval', 300)
            self.user_symbols = self.config.get('user_symbols', [])
            self.top_symbols_count = self.config.get('top_symbols_count', 20)
            self.anomaly_thresholds = self.config.get('anomaly_thresholds', {})
            self.output_config = self.config.get('output', {})
            
            # Set up output directories
            self.reports_dir = self.output_config.get('reports_dir', 'output/reports')
            self.benchmarks_dir = self.output_config.get('benchmarks_dir', 'output/benchmarks')
            
            # Create directories if they don't exist
            Path(self.reports_dir).mkdir(parents=True, exist_ok=True)
            Path(self.benchmarks_dir).mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize orchestrator: {str(e)}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary with configuration parameters
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            # Set default values if not present
            if config is None:
                config = {}
            
            # Set default configuration
            config.setdefault('scan_interval', 300)
            config.setdefault('user_symbols', [])
            config.setdefault('top_symbols_count', 20)
            config.setdefault('anomaly_thresholds', {
                'volume_ratio': 3.0,
                'price_change_ratio': 2.5
            })
            config.setdefault('output', {
                'save_reports': True,
                'reports_dir': 'output/reports',
                'benchmarks_dir': 'output/benchmarks'
            })
            
            return config
            
        except FileNotFoundError:
            print(f"Configuration file {config_path} not found. Using default configuration.")
            return {}
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            return {}
    
    def run_once(self) -> List[Dict[str, Any]]:
        """
        Run the full analysis pipeline once.
        
        Returns:
            List of analysis results with reports
        """
        try:
            print(f"\n{'='*60}")
            print("Running MUST Market Intelligence Agent pipeline...")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Step 1: Run WatcherAgent
            print("\nStep 1: Scanning for market anomalies...")
            
            if self.user_symbols:
                flagged_symbols = self.watcher.scan_for_anomalies(symbols=self.user_symbols)
            else:
                flagged_symbols = self.watcher.scan_for_anomalies()
            
            if not flagged_symbols:
                print("No anomalies detected")
                results = []
            else:
                print(f"Found {len(flagged_symbols)} symbol(s) with anomalies")
                
                # Step 2: Run AnalystAgent
                print("\nStep 2: Analyzing flagged symbols...")
                results = self.analyst.analyze_batch(flagged_symbols)
                
                if results:
                    # Step 3: Run NarratorAgent
                    print("\nStep 3: Generating reports...")
                    reports = self.narrator.generate_batch_reports(results)
                    
                    # Save results to files
                    if self.output_config.get('save_reports', True):
                        self._save_results(reports)
                else:
                    print("No analysis results generated")
            
            print(f"\n{'='*60}")
            print("Pipeline completed successfully!")
            print(f"{'='*60}")
            
            return results
            
        except Exception as e:
            print(f"Error running pipeline: {str(e)}")
            return []
    
    def run_continuous(self):
        """
        Run the pipeline continuously with interval between runs.
        """
        try:
            print(f"\n{'='*60}")
            print("Starting continuous monitoring...")
            print(f"Scan interval: {self.scan_interval} seconds")
            print(f"{'='*60}")
            
            while True:
                try:
                    self.run_once()
                    
                    # Wait for next scan
                    print(f"\nNext scan in {self.scan_interval} seconds...")
                    for remaining in range(self.scan_interval, 0, -1):
                        print(f" {remaining} seconds remaining", end="\r")
                        time.sleep(1)
                    
                except KeyboardInterrupt:
                    print(f"\n\n{'='*60}")
                    print("Continuous monitoring stopped by user.")
                    print(f"{'='*60}")
                    break
                except Exception as e:
                    print(f"Error in continuous run: {str(e)}")
                    print("Waiting 60 seconds before retry...")
                    time.sleep(60)
            
        except KeyboardInterrupt:
            print(f"\n{'='*60}")
            print("Orchestrator stopped.")
            print(f"{'='*60}")
    
    def _save_results(self, reports: List[Dict[str, Any]]) -> None:
        """
        Save analysis results to JSON and text files.
        
        Args:
            reports: List of analysis results with reports
        """
        try:
            # Create timestamped filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_base = f"report_{timestamp}"
            
            # Save JSON file
            json_path = os.path.join(self.reports_dir, f"{filename_base}.json")
            with open(json_path, 'w') as json_file:
                json.dump(reports, json_file, indent=2)
            
            # Save text report
            text_path = os.path.join(self.reports_dir, f"{filename_base}.txt")
            with open(text_path, 'w', encoding='utf-8') as text_file:
                # Create formatted text report
                text_file.write(f"MUST MARKET INTELLIGENCE REPORT\n")
                text_file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                text_file.write(f"{'='*60}\n\n")
                
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
                    
                    text_file.write(f"{emoji} {priority_level} — {symbol} — Score: {final_score:.1f}/100\n")
                    text_file.write(f"{report_text}\n\n")
                
                text_file.write(f"{'='*60}\n")
                text_file.write("Report saved successfully.\n")
                text_file.write(f"{'='*60}\n")
            
            print(f"Results saved to {json_path} and {text_path}")
            
        except Exception as e:
            print(f"Error saving results: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the orchestrator.
        
        Returns:
            Dictionary with status information
        """
        return {
            'scan_interval': self.scan_interval,
            'user_symbols': self.user_symbols,
            'top_symbols_count': self.top_symbols_count,
            'anomaly_thresholds': self.anomaly_thresholds,
            'output_config': self.output_config,
            'reports_dir': self.reports_dir,
            'benchmarks_dir': self.benchmarks_dir
        }
    
    def run_test(self, mock_flagged: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run the analysis pipeline using mock data instead of live anomalies.
        
        Args:
            mock_flagged: List of mock flagged symbols with required fields
            
        Returns:
            List of analysis results with reports
        """
        try:
            print(f"\n{'='*60}")
            print("Running MUST Market Intelligence Agent pipeline...")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Step 1: Skip WatcherAgent, use mock data directly
            print("\nStep 1: Using mock data instead of live anomalies...")
            flagged_symbols = mock_flagged
            
            if not flagged_symbols:
                print("No mock data provided")
                results = []
            else:
                print(f"Found {len(flagged_symbols)} mock symbol(s)")
                
                # Step 2: Run AnalystAgent
                print("\nStep 2: Analyzing mock symbols...")
                results = self.analyst.analyze_batch(flagged_symbols)
                
                if results:
                    # Step 3: Run NarratorAgent
                    print("\nStep 3: Generating reports...")
                    reports = self.narrator.generate_batch_reports(results)
                    
                    # Save results to files
                    if self.output_config.get('save_reports', True):
                        self._save_results(reports)
                else:
                    print("No analysis results generated")
            
            print(f"\n{'='*60}")
            print("Test pipeline completed successfully!")
            print(f"{'='*60}")
            
            return results
            
        except Exception as e:
            print(f"Error running test pipeline: {str(e)}")
            return []


if __name__ == "__main__":
    """
    Test the Orchestrator.
    """
    print("Testing Orchestrator...")
    print("=" * 50)
    
    try:
        # Create orchestrator instance
        orchestrator = Orchestrator()
        
        # Print status
        print("Orchestrator status:")
        status = orchestrator.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\nRunning single pipeline test...")
        results = orchestrator.run_once()
        
        if results:
            print(f"\nGenerated {len(results)} analysis results")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result['symbol']} - {result['priority_level']} - Score: {result['final_score']:.1f}")
        else:
            print("No results generated")
        
        print("\n" + "=" * 50)
        print("Orchestrator test completed!")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        raise