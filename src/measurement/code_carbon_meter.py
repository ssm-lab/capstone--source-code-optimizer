import subprocess
import sys
from codecarbon import EmissionsTracker
from pathlib import Path
import pandas as pd
from os.path import dirname, abspath

REFACTOR_DIR = dirname(abspath(__file__))
sys.path.append(dirname(REFACTOR_DIR))

class CarbonAnalyzer:
    def __init__(self, script_path: str):
        self.script_path = script_path
        self.tracker = EmissionsTracker(allow_multiple_runs=True)

    def run_and_measure(self):
        script = Path(self.script_path)
        if not script.exists() or script.suffix != ".py":
            raise ValueError("Please provide a valid Python script path.")
        self.tracker.start()
        try:
            subprocess.run([sys.executable, str(script)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: The script encountered an error: {e}")
        finally:
            # Stop tracking and get emissions data
            emissions = self.tracker.stop()
            if emissions is None or pd.isna(emissions):
                print("Warning: No valid emissions data collected. Check system compatibility.")
            else:
                print("Emissions data:", emissions)

    def save_report(self, report_path: str = "carbon_report.csv"):
        """
        Save the emissions report to a CSV file with two columns: attribute and value.
        """
        emissions_data = self.tracker.final_emissions_data
        if emissions_data:
            # Convert EmissionsData object to a dictionary and create rows for each attribute
            emissions_dict = emissions_data.__dict__
            attributes = list(emissions_dict.keys())
            values = list(emissions_dict.values())

            # Create a DataFrame with two columns: 'Attribute' and 'Value'
            df = pd.DataFrame({
                "Attribute": attributes,
                "Value": values
            })

            # Save the DataFrame to CSV
            df.to_csv(report_path, index=False)
            print(f"Report saved to {report_path}")
        else:
            print("No data to save. Ensure CodeCarbon supports your system hardware for emissions tracking.")

# Example usage
if __name__ == "__main__":
    analyzer = CarbonAnalyzer("test/inefficent_code_example.py")
    analyzer.run_and_measure()
    analyzer.save_report("test/carbon_report.csv")
