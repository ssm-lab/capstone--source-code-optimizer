import json
from io import StringIO

# ONLY UNCOMMENT IF RUNNING FROM THIS FILE NOT MAIN
# you will need to change imports too
# ======================================================
from os.path import dirname, abspath
import sys
import ast

# Sets src as absolute path, everything needs to be relative to src folder
REFACTOR_DIR = dirname(abspath(__file__))
sys.path.append(dirname(REFACTOR_DIR))

from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from analyzers.base_analyzer import BaseAnalyzer
from refactorer.large_class_refactorer import LargeClassRefactorer
from refactorer.long_lambda_function_refactorer import LongLambdaFunctionRefactorer
from refactorer.long_message_chain_refactorer import LongMessageChainRefactorer

from utils.code_smells import CodeSmells
from utils.ast_parser import parse_line, parse_file

from utils.code_smells import CodeSmells
from utils.ast_parser import parse_line, parse_file


class PylintAnalyzer(BaseAnalyzer):
    def __init__(self, code_path: str):
        super().__init__(code_path)
        # We are going to use the codes to identify the smells this is a dict of all of them

    def analyze(self):
        """
        Runs pylint on the specified Python file and returns the output as a list of dictionaries.
        Each dictionary contains information about a code smell or warning identified by pylint.

        :param file_path: The path to the Python file to be analyzed.
        :return: A list of dictionaries with pylint messages.
        """
        # Capture pylint output into a string stream
        output_stream = StringIO()
        reporter = JSON2Reporter(output_stream)

        # Run pylint
        Run(
            [
                "--max-line-length=80",
                "--max-nested-blocks=3",
                "--max-branches=3",
                "--max-parents=3",
                self.code_path,
            ],
            reporter=reporter,
            exit=False,
        )

        # Retrieve and parse output as JSON
        output = output_stream.getvalue()

        try:
            pylint_results = json.loads(output)
        except json.JSONDecodeError:
            print("Error: Could not decode pylint output")
            pylint_results = []

        print(pylint_results)
        return pylint_results

    def filter_for_all_wanted_code_smells(self, pylint_results):
        statistics = {}
        report = []
        filtered_results = []

        for error in pylint_results:
            if error["messageId"] in CodeSmells.list():
                statistics[error["messageId"]] = True
                filtered_results.append(error)

        report.append(filtered_results)
        report.append(statistics)

        with open("src/output/report.txt", "w+") as f:
            print(json.dumps(report, indent=2), file=f)

        return report

    def filter_for_one_code_smell(self, pylint_results, code):
        filtered_results = []
        for error in pylint_results:
            if error["messageId"] == code:
                filtered_results.append(error)

        return filtered_results


# Example usage
if __name__ == "__main__":

    FILE_PATH = abspath("test/inefficent_code_example.py")

    analyzer = PylintAnalyzer(FILE_PATH)

    # print("THIS IS REPORT for our smells:")
    report = analyzer.analyze()

    with open("src/output/ast.txt", "w+") as f:
        print(parse_file(FILE_PATH), file=f)

    filtered_results = analyzer.filter_for_one_code_smell(report["messages"], "C0301")

    with open(FILE_PATH, "r") as f:
        file_lines = f.readlines()

    for smell in filtered_results:
        with open("src/output/ast_lines.txt", "a+") as f:
            print("Parsing line ", smell["line"], file=f)
            print(parse_line(file_lines, smell["line"]), end="\n", file=f)
