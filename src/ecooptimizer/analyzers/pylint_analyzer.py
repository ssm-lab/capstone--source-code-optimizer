import json
import ast
from io import StringIO
import logging
from pathlib import Path

from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from ecooptimizer.analyzers.base_analyzer import Analyzer
from ecooptimizer.utils.ast_parser import parse_line
from ecooptimizer.utils.analyzers_config import (
    PylintSmell,
    CustomSmell,
    IntermediateSmells,
    EXTRA_PYLINT_OPTIONS,
)

from ecooptimizer.data_wrappers.smell import Smell


class PylintAnalyzer(Analyzer):
    def __init__(self, file_path: Path, source_code: ast.Module):
        super().__init__(file_path, source_code)

    def build_pylint_options(self):
        """
        Constructs the list of pylint options for analysis, including extra options from config.

        :return: List of pylint options for analysis.
        """
        return [str(self.file_path), *EXTRA_PYLINT_OPTIONS]

    def analyze(self):
        """
        Executes pylint on the specified file and captures the output in JSON format.
        """
        if not self.validate_file():
            return

        logging.info(f"Running Pylint analysis on {self.file_path.name}")

        # Capture pylint output in a JSON format buffer
        with StringIO() as buffer:
            reporter = JSON2Reporter(buffer)
            pylint_options = self.build_pylint_options()

            try:
                # Run pylint with JSONReporter
                Run(pylint_options, reporter=reporter, exit=False)

                # Parse the JSON output
                buffer.seek(0)
                self.smells_data = json.loads(buffer.getvalue())["messages"]
                logging.info("Pylint analyzer completed successfully.")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON output from pylint: {e}")
            except Exception as e:
                logging.error(f"An error occurred during pylint analysis: {e}")

        logging.info("Running custom parsers:")

        lmc_data = self.detect_long_message_chain()
        self.smells_data.extend(lmc_data)

        uva_data = self.detect_unused_variables_and_attributes()
        self.smells_data.extend(uva_data)

    def configure_smells(self):
        """
        Filters the report data to retrieve only the smells with message IDs specified in the config.
        """
        logging.info("Filtering pylint smells")

        configured_smells: list[Smell] = []

        for smell in self.smells_data:
            if smell["messageId"] in PylintSmell.list():
                configured_smells.append(smell)
            elif smell["messageId"] in CustomSmell.list():
                configured_smells.append(smell)

            if smell["messageId"] == IntermediateSmells.LINE_TOO_LONG.value:
                self.filter_ternary(smell)
                self.filter_long_lambda(smell)

        self.smells_data = configured_smells

    def filter_for_one_code_smell(self, pylint_results: list[Smell], code: str):
        filtered_results: list[Smell] = []
        for error in pylint_results:
            if error["messageId"] == code:  # type: ignore
                filtered_results.append(error)

        return filtered_results

    def filter_ternary(self, smell: Smell):
        """
        Filters LINE_TOO_LONG smells to find ternary expression smells
        """
        root_node = parse_line(self.file_path, smell["line"])

        if root_node is None:
            return

        for node in ast.walk(root_node):
            if isinstance(node, ast.IfExp):  # Ternary expression node
                smell["messageId"] = CustomSmell.LONG_TERN_EXPR.value
                smell["message"] = "Ternary expression has too many branches"
                self.smells_data.append(smell)
                break

    def filter_long_lambda(self, smell: Smell, max_length: int = 100):
        """
        Filters LINE_TOO_LONG smells to find long lambda functions.
        Args:
        - smell: The Smell object representing a LINE_TOO_LONG error.
        - max_length: The maximum allowed line length for lambda functions.
                    Note this is dependent on pylint flagging "line too long"
                    so by pylint the min is 100 to sucessfully detect
        """
        root_node = parse_line(self.file_path, smell["line"])

        if root_node is None:
            return

        for node in ast.walk(root_node):
            if isinstance(node, ast.Lambda):  # Lambda function node
                # Check the length of the line containing the lambda
                line_length = len(smell.get("message", ""))
                if line_length > max_length:
                    smell["messageId"] = CustomSmell.LONG_LAMBDA_EXPR.value
                    smell["message"] = f"Lambda function too long ({line_length}/{max_length})"
                    self.smells_data.append(smell)
                    break

    def detect_long_message_chain(self, threshold: int = 3):
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
        results: list[Smell] = []
        used_lines = set()

        # Function to detect long chains
        def check_chain(node: ast.Attribute | ast.expr, chain_length: int = 0):
            # If the chain length exceeds the threshold, add it to results
            if chain_length >= threshold:
                # Create the message for the convention
                message = f"Method chain too long ({chain_length}/{threshold})"
                # Add the result in the required format

                result: Smell = {
                    "absolutePath": str(self.file_path),
                    "column": node.col_offset,
                    "confidence": "UNDEFINED",
                    "endColumn": None,
                    "endLine": None,
                    "line": node.lineno,
                    "message": message,
                    "messageId": CustomSmell.LONG_MESSAGE_CHAIN.value,
                    "module": self.file_path.name,
                    "obj": "",
                    "path": str(self.file_path),
                    "symbol": "long-message-chain",
                    "type": "convention",
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
        for node in ast.walk(self.source_code):
            # We are only interested in method calls (attribute access)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                # Call check_chain to detect long chains
                check_chain(node.func)

        return results

    def detect_unused_variables_and_attributes(self):
        """
        Detects unused variables and class attributes in the given Python code and returns a list of results.

        Args:
        - code (str): Python source code to be analyzed.
        - file_path (str): The path to the file being analyzed (for reporting purposes).
        - module_name (str): The name of the module (for reporting purposes).

        Returns:
        - List of dictionaries: Each dictionary contains details about the detected unused variable or attribute.
        """
        # Store variable and attribute declarations and usage
        declared_vars = set()
        used_vars = set()
        results: list[Smell] = []

        # Helper function to gather declared variables (including class attributes)
        def gather_declarations(node: ast.AST):
            # For assignment statements (variables or class attributes)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):  # Simple variable
                        declared_vars.add(target.id)
                    elif isinstance(target, ast.Attribute):  # Class attribute
                        declared_vars.add(f"{target.value.id}.{target.attr}")  # type: ignore

            # For class attribute assignments (e.g., self.attribute)
            elif isinstance(node, ast.ClassDef):
                for class_node in ast.walk(node):
                    if isinstance(class_node, ast.Assign):
                        for target in class_node.targets:
                            if isinstance(target, ast.Name):
                                declared_vars.add(target.id)
                            elif isinstance(target, ast.Attribute):
                                declared_vars.add(f"{target.value.id}.{target.attr}")  # type: ignore

        # Helper function to gather used variables and class attributes
        def gather_usages(node: ast.AST):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):  # Variable usage
                used_vars.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(
                node.ctx, ast.Load
            ):  # Attribute usage
                # Check if the attribute is accessed as `self.attribute`
                if isinstance(node.value, ast.Name) and node.value.id == "self":
                    # Only add to used_vars if it’s in the form of `self.attribute`
                    used_vars.add(f"self.{node.attr}")

        # Gather declared and used variables
        for node in ast.walk(self.source_code):
            gather_declarations(node)
            gather_usages(node)

        # Detect unused variables by finding declared variables not in used variables
        unused_vars = declared_vars - used_vars

        for var in unused_vars:
            # Locate the line number for each unused variable or attribute
            line_no, column_no = 0, 0
            symbol = ""
            for node in ast.walk(self.source_code):
                if isinstance(node, ast.Name) and node.id == var:
                    line_no = node.lineno
                    column_no = node.col_offset
                    symbol = "unused-variable"
                    break
                elif (
                    isinstance(node, ast.Attribute)
                    and f"self.{node.attr}" == var
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "self"
                ):
                    line_no = node.lineno
                    column_no = node.col_offset
                    symbol = "unused-attribute"
                    break

            result: Smell = {
                "absolutePath": str(self.file_path),
                "column": column_no,
                "confidence": "UNDEFINED",
                "endColumn": None,
                "endLine": None,
                "line": line_no,
                "message": f"Unused variable or attribute '{var}'",
                "messageId": CustomSmell.UNUSED_VAR_OR_ATTRIBUTE.value,
                "module": self.file_path.name,
                "obj": "",
                "path": str(self.file_path),
                "symbol": symbol,
                "type": "convention",
            }

            results.append(result)

        return results
