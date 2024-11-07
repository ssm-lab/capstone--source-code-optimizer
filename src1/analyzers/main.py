"""
A simple main.py to demonstrate the usage of various functions in the analyzer classes.
This script runs different analyzers and outputs results as JSON files in the `main_output`
folder. This helps to understand how the analyzers work and allows viewing the details of 
detected code smells and configured refactorable smells.

Each output JSON file provides insight into the raw data returned by PyLint and custom analyzers, 
which is useful for debugging and verifying functionality. Note: In the final implementation, 
we may not output these JSON files, but they are useful for demonstration purposes.

INSTRUCTIONS TO RUN THIS FILE:
1. Change directory to the `src` folder: cd src
2. Run the script using the following command: python -m analyzers.main
3. Optional: Specify a test file path (absolute path) as an argument to override the default test case
(`inefficient_code_example_1.py`). For example: python -m analyzers.main <test_file_path>
"""

import os
import json
import sys
from analyzers.pylint_analyzer import PylintAnalyzer
from analyzers.ternary_expression_analyzer import TernaryExpressionAnalyzer
from utils.analyzers_config import AllSmells

# Define the output folder within the analyzers package
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'code_smells')

# Ensure the output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def save_to_file(data, filename):
    """
    Saves JSON data to a file in the output folder.

    :param data: Data to be saved.
    :param filename: Name of the file to save data to.
    """
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    with open(filepath, 'w') as file:
        json.dump(data, file, sort_keys=True, indent=4)
    print(f"Output saved to {filepath}")

def run_pylint_analysis(file_path):
    print("\nStarting pylint analysis...")

    # Create an instance of PylintAnalyzer and run analysis
    pylint_analyzer = PylintAnalyzer(file_path)
    pylint_analyzer.analyze()

    # Save all detected smells to file
    all_smells = pylint_analyzer.get_all_detected_smells()
    save_to_file(all_smells, 'pylint_all_smells.json')

    # Example: Save only configured smells to file
    configured_smells = pylint_analyzer.get_configured_smells()
    save_to_file(configured_smells, 'pylint_configured_smells.json')

    # Example: Save smells specific to "LINE_TOO_LONG"
    line_too_long_smells = pylint_analyzer.get_smells_by_name(AllSmells.LINE_TOO_LONG)
    save_to_file(line_too_long_smells, 'pylint_line_too_long_smells.json')


def run_ternary_expression_analysis(file_path, max_length=50):
    print("\nStarting ternary expression analysis...")

    # Create an instance of TernaryExpressionAnalyzer and run analysis
    ternary_analyzer = TernaryExpressionAnalyzer(file_path, max_length)
    ternary_analyzer.analyze()

    # Save all long ternary expressions to file
    long_expressions = ternary_analyzer.get_all_detected_smells()
    save_to_file(long_expressions, 'ternary_long_expressions.json')

    # Example: Save filtered expressions based on a custom length threshold
    min_length = 70
    filtered_expressions = ternary_analyzer.filter_expressions_by_length(min_length)
    save_to_file(filtered_expressions, f'ternary_expressions_min_length_{min_length}.json')


def main():
    # Get the file path from command-line arguments if provided, otherwise use the default
    default_test_file = os.path.join(os.path.dirname(__file__), "../../src1-tests/ineffcient_code_example_1.py")
    test_file = sys.argv[1] if len(sys.argv) > 1 else default_test_file

    # Check if the file exists
    if not os.path.isfile(test_file):
        print(f"Error: The file '{test_file}' does not exist.")
        return

    # Run examples of PylintAnalyzer usage
    run_pylint_analysis(test_file)

    # Run examples of TernaryExpressionAnalyzer usage
    run_ternary_expression_analysis(test_file, max_length=50)

if __name__ == "__main__":
    main()
