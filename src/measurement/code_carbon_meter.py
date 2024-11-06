import subprocess
import sys
from codecarbon import EmissionsTracker
from pathlib import Path

# To run run
# pip install codecarbon
from os.path import dirname, abspath
import sys

# Sets src as absolute path, everything needs to be relative to src folder
REFACTOR_DIR = dirname(abspath(__file__))
sys.path.append(dirname(REFACTOR_DIR))


class CarbonAnalyzer:
    def __init__(self, script_path: str):
        """
        Initialize with the path to the Python script to analyze.
        """
        self.script_path = script_path
        self.tracker = EmissionsTracker(allow_multiple_runs=True)

    def run_and_measure(self):
        """
        Run the specified Python script and measure its energy consumption and CO2 emissions.
        """
        script = Path(self.script_path)

        # Check if the file exists and is a Python file
        if not script.exists() or script.suffix != ".py":
            raise ValueError("Please provide a valid Python script path.")

        # Start tracking emissions
        self.tracker.start()

        try:
            # Run the Python script as a subprocess
            subprocess.run(["python", str(script)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: The script encountered an error: {e}")
        finally:
            # Stop tracking and get emissions data
            emissions = self.tracker.stop()
            print("Emissions data:", emissions)

    def save_report(self, report_path: str = "carbon_report.csv"):
        """
        Save the emissions report to a CSV file.
        """
        import pandas as pd

        data = self.tracker.emissions_data
        if data:
            df = pd.DataFrame(data)
            print("THIS IS THE DF:")
            print(df)
            df.to_csv(report_path, index=False)
            print(f"Report saved to {report_path}")
        else:
            print("No data to save.")


# Example usage
if __name__ == "__main__":
    analyzer = CarbonAnalyzer("test/inefficent_code_example.py")
    analyzer.run_and_measure()
    analyzer.save_report("test/carbon_report.csv")
