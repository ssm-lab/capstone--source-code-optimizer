import json
import ast
import os

from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter

from io import StringIO

from utils.logger import Logger

from .base_analyzer import Analyzer
from utils.analyzers_config import (
    PylintSmell,
    CustomSmell,
    IntermediateSmells,
    EXTRA_PYLINT_OPTIONS,
)

from utils.ast_parser import parse_line


class PylintAnalyzer(Analyzer):
    def __init__(self, file_path: str, logger: Logger):
        super().__init__(file_path, logger)

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
            return

        self.logger.log(
            f"Running Pylint analysis on {os.path.basename(self.file_path)}"
        )

        # Capture pylint output in a JSON format buffer
        with StringIO() as buffer:
            reporter = JSONReporter(buffer)
            pylint_options = self.build_pylint_options()

            try:
                # Run pylint with JSONReporter
                Run(pylint_options, reporter=reporter, exit=False)

                # Parse the JSON output
                buffer.seek(0)
                self.smells_data = json.loads(buffer.getvalue())
                self.logger.log("Pylint analyzer completed successfully.")
            except json.JSONDecodeError as e:
                self.logger.log(f"Failed to parse JSON output from pylint: {e}")
            except Exception as e:
                self.logger.log(f"An error occurred during pylint analysis: {e}")

        self.logger.log("Running custom parsers:")
        lmc_data = PylintAnalyzer.detect_long_message_chain(
            PylintAnalyzer.read_code_from_path(self.file_path),
            self.file_path,
            os.path.basename(self.file_path),
        )
        print("THIS IS LMC DATA:", lmc_data)
        self.smells_data += lmc_data

    def configure_smells(self):
        """
        Filters the report data to retrieve only the smells with message IDs specified in the config.
        """
        self.logger.log("Filtering pylint smells")

        configured_smells: list[object] = []

        for smell in self.smells_data:
            if smell["message-id"] in PylintSmell.list():
                configured_smells.append(smell)
            elif smell["message-id"] in CustomSmell.list():
                configured_smells.append(smell)

            if smell["message-id"] == IntermediateSmells.LINE_TOO_LONG.value:
                self.filter_ternary(smell)

        self.smells_data = configured_smells

    def filter_for_one_code_smell(self, pylint_results: list[object], code: str):
        filtered_results: list[object] = []
        for error in pylint_results:
            if error["message-id"] == code:
                filtered_results.append(error)

        return filtered_results

    def filter_ternary(self, smell: object):
        """
        Filters LINE_TOO_LONG smells to find ternary expression smells
        """
        root_node = parse_line(self.file_path, smell["line"])

        if root_node is None:
            return

        for node in ast.walk(root_node):
            if isinstance(node, ast.IfExp):  # Ternary expression node
                smell["message-id"] = CustomSmell.LONG_TERN_EXPR.value
                smell["message"] = "Ternary expression has too many branches"
                self.smells_data.append(smell)
                break

    def detect_long_message_chain(code, file_path, module_name, threshold=3):
        """
        Detects long message chains in the given Python code and returns a list of results.

        Args:
        - code (str): Python source code to be analyzed.
        - file_path (str): The path to the file being analyzed (for reporting purposes).
        - module_name (str): The name of the module (for reporting purposes).
        - threshold (int): The minimum number of chained method calls to flag as a long chain.

        Returns:
        - List of dictionaries: Each dictionary contains details about the detected long chain.
        """
        # Parse the code into an Abstract Syntax Tree (AST)
        tree = ast.parse(code)

        results = []
        used_lines = set()

        # Function to detect long chains
        def check_chain(node, chain_length=0):
            # If the chain length exceeds the threshold, add it to results
            if chain_length >= threshold:
                # Create the message for the convention
                message = f"Method chain too long ({chain_length}/{threshold})"
                # Add the result in the required format
                result = {
                    "type": "convention",
                    "symbol": "long-message-chain",
                    "message": message,
                    "message-id": "LMC001",
                    "confidence": "UNDEFINED",
                    "module": module_name,
                    "obj": "",
                    "line": node.lineno,
                    "column": node.col_offset,
                    "endLine": None,
                    "endColumn": None,
                    "path": file_path,
                    "absolutePath": file_path,  # Assuming file_path is the absolute path
                }

                if node.lineno in used_lines:
                    return
                used_lines.add(node.lineno)
                results.append(result)
                return

            if isinstance(node, ast.Call):
                # If the node is a function call, increment the chain length
                chain_length += 1
                # Recursively check if there's a chain in the function being called
                if isinstance(node.func, ast.Attribute):
                    check_chain(node.func, chain_length)

            elif isinstance(node, ast.Attribute):
                # Increment chain length for attribute access (part of the chain)
                chain_length += 1
                check_chain(node.value, chain_length)

        # Walk through the AST
        for node in ast.walk(tree):
            # We are only interested in method calls (attribute access)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                # Call check_chain to detect long chains
                check_chain(node.func)

        return results

    @staticmethod
    def read_code_from_path(file_path):
        """
        Reads the Python code from a given file path.

        Args:
        - file_path (str): The path to the Python file.

        Returns:
        - str: The content of the file as a string.
        """
        try:
            with open(file_path, "r") as file:
                code = file.read()
            return code
        except FileNotFoundError:
            print(f"Error: The file at {file_path} was not found.")
            return None
        except IOError as e:
            print(f"Error reading file {file_path}: {e}")
            return None
