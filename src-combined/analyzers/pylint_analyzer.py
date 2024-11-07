import json
from io import StringIO
import ast
from re import sub
# ONLY UNCOMMENT IF RUNNING FROM THIS FILE NOT MAIN
# you will need to change imports too
# ======================================================
# from os.path import dirname, abspath
# import sys


# # Sets src as absolute path, everything needs to be relative to src folder
# REFACTOR_DIR = dirname(abspath(__file__))
# sys.path.append(dirname(REFACTOR_DIR))

from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from analyzers.base_analyzer import Analyzer

from utils.analyzers_config import EXTRA_PYLINT_OPTIONS, CustomSmell, PylintSmell
from utils.analyzers_config import IntermediateSmells
from utils.ast_parser import parse_line

class PylintAnalyzer(Analyzer):
    def __init__(self, code_path: str):
        super().__init__(code_path)

    def build_pylint_options(self):
        """
        Constructs the list of pylint options for analysis, including extra options from config.

        :return: List of pylint options for analysis.
        """
        return [self.file_path] + EXTRA_PYLINT_OPTIONS
        
    def analyze(self):
        """
        Executes pylint on the specified file and captures the output in JSON format.
        """
        if not self.validate_file():
            print(f"File not found: {self.file_path}")
            return

        print(f"Running pylint analysis on {self.file_path}")

        # Capture pylint output in a JSON format buffer
        with StringIO() as buffer:
            reporter = JSON2Reporter(buffer)
            pylint_options = self.build_pylint_options()

            try:
                # Run pylint with JSONReporter
                Run(pylint_options, reporter=reporter, exit=False)

                # Parse the JSON output
                buffer.seek(0)
                self.report_data = json.loads(buffer.getvalue())
                print("Pylint JSON analysis completed.")
            except json.JSONDecodeError as e:
                print("Failed to parse JSON output from pylint:", e)
            except Exception as e:
                print("An error occurred during pylint analysis:", e)

    def get_configured_smells(self):
        filtered_results: list[object] = []

        for error in self.report_data["messages"]:
            if error["messageId"] in PylintSmell.list():
                filtered_results.append(error)

        for smell in IntermediateSmells.list():
            temp_smells = self.filter_for_one_code_smell(self.report_data["messages"], smell)

            if smell == IntermediateSmells.LINE_TOO_LONG.value:
                filtered_results.extend(self.filter_long_lines(temp_smells))
        
        with open("src/output/report.txt", "w+") as f:
            print(json.dumps(filtered_results, indent=2), file=f)

        return filtered_results

    def filter_for_one_code_smell(self, pylint_results: list[object], code: str):
        filtered_results: list[object] = []
        for error in pylint_results:
            if error["messageId"] == code:
                filtered_results.append(error)

        return filtered_results
    
    def filter_long_lines(self, long_line_smells: list[object]):
        selected_smells: list[object] = []
        for smell in long_line_smells:    
            root_node = parse_line(self.file_path, smell["line"])

            if root_node is None:
                continue

            for node in ast.walk(root_node):
                if isinstance(node, ast.IfExp):  # Ternary expression node
                    smell["messageId"] = CustomSmell.LONG_TERN_EXPR.value
                    selected_smells.append(smell)
                    break
                    
        return selected_smells

# Example usage
# if __name__ == "__main__":

#     FILE_PATH = abspath("test/inefficent_code_example.py")

#     analyzer = PylintAnalyzer(FILE_PATH)

#     # print("THIS IS REPORT for our smells:")
#     report = analyzer.analyze()

#     with open("src/output/ast.txt", "w+") as f:
#         print(parse_file(FILE_PATH), file=f)

#     filtered_results = analyzer.filter_for_one_code_smell(report["messages"], "C0301")


#     with open(FILE_PATH, "r") as f:
#         file_lines = f.readlines()

#     for smell in filtered_results:
#         with open("src/output/ast_lines.txt", "a+") as f:
#             print("Parsing line ", smell["line"], file=f)
#             print(parse_line(file_lines, smell["line"]), end="\n", file=f)
        


    
