import json
import os
import sys

from analyzers.pylint_analyzer import PylintAnalyzer
from measurement.code_carbon_meter import CarbonAnalyzer
from utils.factory import RefactorerFactory

DIRNAME = os.path.dirname(__file__)

# Define the output folder within the analyzers package
OUTPUT_FOLDER = os.path.join(DIRNAME, 'output/')

# Ensure the output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def save_to_file(data, filename):
    """
    Saves JSON data to a file in the output folder.

    :param data: Data to be saved.
    :param filename: Name of the file to save data to.
    """
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    with open(filepath, 'w+') as file:
        json.dump(data, file, sort_keys=True, indent=4)
    print(f"Output saved to {filepath.removeprefix(DIRNAME)}")

def run_pylint_analysis(test_file_path):
    print("\nStarting pylint analysis...")

    # Create an instance of PylintAnalyzer and run analysis
    pylint_analyzer = PylintAnalyzer(test_file_path)
    pylint_analyzer.analyze()

    # Save all detected smells to file
    all_smells = pylint_analyzer.get_all_detected_smells()
    save_to_file(all_smells["messages"], 'pylint_all_smells.json')

    # Example: Save only configured smells to file
    configured_smells = pylint_analyzer.get_configured_smells()
    save_to_file(configured_smells, 'pylint_configured_smells.json')

    return configured_smells

def main():
    """
    Entry point for the refactoring tool.
    - Create an instance of the analyzer.
    - Perform code analysis and print the results.
    """

    # Get the file path from command-line arguments if provided, otherwise use the default
    DEFAULT_TEST_FILE = os.path.join(DIRNAME, "../test/inefficent_code_example.py")
    TEST_FILE = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEST_FILE

    # Check if the test file exists
    if not os.path.isfile(TEST_FILE):
        print(f"Error: The file '{TEST_FILE}' does not exist.")
        return

    INITIAL_REPORT_FILE_PATH = os.path.join(OUTPUT_FOLDER, "initial_carbon_report.csv")

    carbon_analyzer = CarbonAnalyzer(TEST_FILE)
    carbon_analyzer.run_and_measure()
    carbon_analyzer.save_report(INITIAL_REPORT_FILE_PATH)

    detected_smells = run_pylint_analysis(TEST_FILE)

    for smell in detected_smells:
        smell_id: str = smell["messageId"]

        print("Refactoring ", smell_id)
        refactoring_class = RefactorerFactory.build(smell_id, TEST_FILE)

        if refactoring_class:
            refactoring_class.refactor()
        else:
            raise NotImplementedError("This refactoring has not been implemented yet.")


if __name__ == "__main__":
    main()
