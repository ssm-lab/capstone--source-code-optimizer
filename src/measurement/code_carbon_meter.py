import subprocess
import sys
from codecarbon import EmissionsTracker
from pathlib import Path
import pandas as pd

from os.path import dirname, abspath
import sys

# FOR TESTING!!! Not necessary when running from main
# Sets src as absolute path, everything needs to be relative to src folder
REFACTOR_DIR = dirname(abspath(__file__))
sys.path.append(dirname(REFACTOR_DIR))

# To run run
# pip install codecarbon
from os.path import dirname, abspath
import sys

# Sets src as absolute path, everything needs to be relative to src folder
REFACTOR_DIR = dirname(abspath(__file__))
sys.path.append(dirname(REFACTOR_DIR))


class CarbonAnalyzer:
    def __init__(self, script_path: str, report_path: str):
        """
        Initialize with the path to the Python script to analyze.
        """
        self.script_path = script_path
        self.tracker = EmissionsTracker(allow_multiple_runs=True, output_file=report_path)

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

    def save_report(self, report_path: str):
        """
        Save the emissions report to a CSV file.
        """
        data = self.tracker.final_emissions_data
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

    TEST_FILE_PATH = abspath("test/inefficent_code_example.py")
    REPORT_FILE_PATH = abspath("src/output/carbon_report.csv")
    
    analyzer = CarbonAnalyzer(TEST_FILE_PATH, REPORT_FILE_PATH)
    analyzer.run_and_measure()
    analyzer.save_report(REPORT_FILE_PATH)
