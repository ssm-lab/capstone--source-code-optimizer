from collections import defaultdict
import json
import ast
from io import StringIO
import logging
from pathlib import Path

import astor
from pylint.lint import Run
from pylint.reporters.json_reporter import JSON2Reporter

from .base_analyzer import Analyzer
from ..utils.analyzers_config import (
    PylintSmell,
    CustomSmell,
    EXTRA_PYLINT_OPTIONS,
)
from ..data_wrappers.smell import LECSmell, LLESmell, LMCSmell, Smell, CRCSmell, UVASmell

from .custom_checkers.str_concat_in_loop import StringConcatInLoopChecker


class PylintAnalyzer(Analyzer):
    def __init__(self, file_path: Path, source_code: ast.Module):
        super().__init__(file_path, source_code)

    def build_pylint_options(self):
        """
        Constructs the list of pylint options for analysis, including extra options from config.

        :return: List of pylint options for analysis.
        """
        return [str(self.file_path), *EXTRA_PYLINT_OPTIONS]

    def build_smells(self, pylint_smells: dict):  # type: ignore
        """Casts inital list of pylint smells to the proper Smell configuration."""
        for smell in pylint_smells:
            self.smells_data.append(
                {
                    "confidence": smell["confidence"],
                    "message": smell["message"],
                    "messageId": smell["messageId"],
                    "module": smell["module"],
                    "obj": smell["obj"],
                    "path": smell["absolutePath"],
                    "symbol": smell["symbol"],
                    "type": smell["type"],
                    "occurences": [
                        {
                            "line": smell["line"],
                            "endLine": smell["endLine"],
                            "column": smell["column"],
                            "endColumn": smell["endColumn"],
                        }
                    ],
                    "additionalInfo": None,
                }
            )

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
                self.build_smells(json.loads(buffer.getvalue())["messages"])
                logging.info("Pylint analyzer completed successfully.")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON output from pylint: {e}")
            except Exception as e:
                logging.error(f"An error occurred during pylint analysis: {e}")

        logging.info("Running custom parsers:")

        lmc_data = self.detect_long_message_chain()
        self.smells_data.extend(lmc_data)

        llf_data = self.detect_long_lambda_expression()
        self.smells_data.extend(llf_data)

        uva_data = self.detect_unused_variables_and_attributes()
        self.smells_data.extend(uva_data)

        lec_data = self.detect_long_element_chain()
        self.smells_data.extend(lec_data)

        scl_checker = StringConcatInLoopChecker(self.file_path)
        self.smells_data.extend(scl_checker.smells)

        crc_checker = self.detect_repeated_calls()
        self.smells_data.extend(crc_checker)

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

            # if smell["messageId"] == IntermediateSmells.LINE_TOO_LONG.value:
            #     self.filter_ternary(smell)

        self.smells_data = configured_smells

    def filter_for_one_code_smell(self, pylint_results: list[Smell], code: str):
        filtered_results: list[Smell] = []
        for error in pylint_results:
            if error["messageId"] == code:  # type: ignore
                filtered_results.append(error)

        return filtered_results

    # def filter_ternary(self, smell: Smell):
    #     """
    #     Filters LINE_TOO_LONG smells to find ternary expression smells
    #     """
    #     root_node = parse_line(self.file_path, smell["line"])

    #     if root_node is None:
    #         return

    #     for node in ast.walk(root_node):
    #         if isinstance(node, ast.IfExp):  # Ternary expression node
    #             smell["messageId"] = CustomSmell.LONG_TERN_EXPR.value
    #             smell["message"] = "Ternary expression has too many branches"
    #             self.smells_data.append(smell)
    #             break

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
        results: list[LMCSmell] = []
        used_lines = set()

        # Function to detect long chains
        def check_chain(node: ast.Attribute | ast.expr, chain_length: int = 0):
            # If the chain length exceeds the threshold, add it to results
            if chain_length >= threshold:
                # Create the message for the convention
                message = f"Method chain too long ({chain_length}/{threshold})"
                # Add the result in the required format

                result: LMCSmell = {
                    "path": str(self.file_path),
                    "module": self.file_path.stem,
                    "obj": None,
                    "type": "convention",
                    "symbol": "",
                    "message": message,
                    "messageId": CustomSmell.LONG_MESSAGE_CHAIN,
                    "confidence": "UNDEFINED",
                    "occurences": [
                        {
                            "line": node.lineno,
                            "endLine": node.end_lineno,
                            "column": node.col_offset,
                            "endColumn": node.end_col_offset,
                        }
                    ],
                    "additionalInfo": None,
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

    def detect_long_lambda_expression(self, threshold_length: int = 100, threshold_count: int = 3):
        """
        Detects lambda functions that are too long, either by the number of expressions or the total length in characters.
        Returns a list of results.

        Args:
        - threshold_length (int): The maximum number of characters allowed in the lambda expression.
        - threshold_count (int): The maximum number of expressions allowed inside the lambda function.

        Returns:
        - List of dictionaries: Each dictionary contains details about the detected long lambda.
        """
        results: list[LLESmell] = []
        used_lines = set()

        # Function to check the length of lambda expressions
        def check_lambda(node: ast.Lambda):
            # Count the number of expressions in the lambda body
            if isinstance(node.body, list):
                lambda_length = len(node.body)
            else:
                lambda_length = 1  # Single expression if it's not a list
            print("this is length", lambda_length)
            # Check if the lambda expression exceeds the threshold based on the number of expressions
            if lambda_length >= threshold_count:
                message = (
                    f"Lambda function too long ({lambda_length}/{threshold_count} expressions)"
                )

                result: LLESmell = {
                    "path": str(self.file_path),
                    "module": self.file_path.stem,
                    "obj": None,
                    "type": "convention",
                    "symbol": "long-lambda-expr",
                    "message": message,
                    "messageId": CustomSmell.LONG_LAMBDA_EXPR,
                    "confidence": "UNDEFINED",
                    "occurences": [
                        {
                            "line": node.lineno,
                            "endLine": node.end_lineno,
                            "column": node.col_offset,
                            "endColumn": node.end_col_offset,
                        }
                    ],
                    "additionalInfo": None,
                }

                if node.lineno in used_lines:
                    return
                used_lines.add(node.lineno)
                results.append(result)

            # Convert the lambda function to a string and check its total length in characters
            lambda_code = get_lambda_code(node)
            print(lambda_code)
            print("this is length of char: ", len(lambda_code))
            if len(lambda_code) > threshold_length:
                message = f"Lambda function too long ({len(lambda_code)} characters, max {threshold_length})"
                result: LLESmell = {
                    "path": str(self.file_path),
                    "module": self.file_path.stem,
                    "obj": None,
                    "type": "convention",
                    "symbol": "long-lambda-expr",
                    "message": message,
                    "messageId": CustomSmell.LONG_LAMBDA_EXPR,
                    "confidence": "UNDEFINED",
                    "occurences": [
                        {
                            "line": node.lineno,
                            "endLine": node.end_lineno,
                            "column": node.col_offset,
                            "endColumn": node.end_col_offset,
                        }
                    ],
                    "additionalInfo": None,
                }

                if node.lineno in used_lines:
                    return
                used_lines.add(node.lineno)
                results.append(result)

        # Helper function to get the string representation of the lambda expression
        def get_lambda_code(lambda_node: ast.Lambda) -> str:
            # Reconstruct the lambda arguments and body as a string
            args = ", ".join(arg.arg for arg in lambda_node.args.args)

            # Convert the body to a string by using ast's built-in functionality
            body = ast.unparse(lambda_node.body)

            # Combine to form the lambda expression
            return f"lambda {args}: {body}"

        # Walk through the AST to find lambda expressions
        for node in ast.walk(self.source_code):
            if isinstance(node, ast.Lambda):
                print("found a lambda")
                check_lambda(node)

        return results

    def detect_unused_variables_and_attributes(self):
        """
        Detects unused variables and class attributes in the given Python code and returns a list of results.

        Returns:
        - List of dictionaries: Each dictionary contains details about the detected unused variable or attribute.
        """
        # Store variable and attribute declarations and usage
        declared_vars = set()
        used_vars = set()
        results: list[UVASmell] = []

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
            var_node = None
            symbol = ""
            for node in ast.walk(self.source_code):
                if isinstance(node, ast.Name) and node.id == var:
                    symbol = "unused-variable"
                    var_node = node
                    break
                elif (
                    isinstance(node, ast.Attribute)
                    and f"self.{node.attr}" == var
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "self"
                ):
                    symbol = "unused-attribute"
                    var_node = node
                    break

            if var_node:
                result: UVASmell = {
                    "path": str(self.file_path),
                    "module": self.file_path.stem,
                    "obj": None,
                    "type": "convention",
                    "symbol": symbol,
                    "message": f"Unused variable or attribute '{var}'",
                    "messageId": CustomSmell.UNUSED_VAR_OR_ATTRIBUTE,
                    "confidence": "UNDEFINED",
                    "occurences": [
                        {
                            "line": var_node.lineno,
                            "endLine": var_node.end_lineno,
                            "column": var_node.col_offset,
                            "endColumn": var_node.end_col_offset,
                        }
                    ],
                    "additionalInfo": None,
                }

                results.append(result)

        return results

    def detect_long_element_chain(self, threshold: int = 3):
        """
        Detects long element chains in the given Python code and returns a list of results.

        Returns:
        - List of dictionaries: Each dictionary contains details about the detected long chain.
        """
        # Parse the code into an Abstract Syntax Tree (AST)
        results: list[LECSmell] = []
        used_lines = set()

        # Function to calculate the length of a dictionary chain
        def check_chain(node: ast.Subscript, chain_length: int = 0):
            current = node
            while isinstance(current, ast.Subscript):
                chain_length += 1
                current = current.value

            if chain_length >= threshold:
                # Create the message for the convention
                message = f"Dictionary chain too long ({chain_length}/{threshold})"

                result: LECSmell = {
                    "path": str(self.file_path),
                    "module": self.file_path.stem,
                    "obj": None,
                    "type": "convention",
                    "symbol": "long-element-chain",
                    "message": message,
                    "messageId": CustomSmell.LONG_ELEMENT_CHAIN,
                    "confidence": "UNDEFINED",
                    "occurences": [
                        {
                            "line": node.lineno,
                            "endLine": node.end_lineno,
                            "column": node.col_offset,
                            "endColumn": node.end_col_offset,
                        }
                    ],
                    "additionalInfo": None,
                }

                if node.lineno in used_lines:
                    return
                used_lines.add(node.lineno)
                results.append(result)

        # Walk through the AST
        for node in ast.walk(self.source_code):
            if isinstance(node, ast.Subscript):
                check_chain(node)

        return results

    def detect_repeated_calls(self, threshold: int = 2):
        results: list[CRCSmell] = []

        tree = self.source_code

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.For, ast.While)):
                call_counts: dict[str, list[ast.Call]] = defaultdict(list)
                modified_lines = set()

                for subnode in ast.walk(node):
                    if isinstance(subnode, (ast.Assign, ast.AugAssign)):
                        # targets = [target.id for target in getattr(subnode, "targets", []) if isinstance(target, ast.Name)]
                        modified_lines.add(subnode.lineno)

                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        call_string = astor.to_source(subnode).strip()
                        call_counts[call_string].append(subnode)

                for call_string, occurrences in call_counts.items():
                    if len(occurrences) >= threshold:
                        skip_due_to_modification = any(
                            line in modified_lines
                            for start_line, end_line in zip(
                                [occ.lineno for occ in occurrences[:-1]],
                                [occ.lineno for occ in occurrences[1:]],
                            )
                            for line in range(start_line + 1, end_line)
                        )

                        if skip_due_to_modification:
                            continue

                        smell: CRCSmell = {
                            "path": str(self.file_path),
                            "module": self.file_path.stem,
                            "obj": None,
                            "type": "performance",
                            "symbol": "cached-repeated-calls",
                            "message": f"Repeated function call detected ({len(occurrences)}/{threshold}). "
                            f"Consider caching the result: {call_string}",
                            "messageId": CustomSmell.CACHE_REPEATED_CALLS,
                            "confidence": "HIGH" if len(occurrences) > threshold else "MEDIUM",
                            "occurences": [
                                {
                                    "line": occ.lineno,
                                    "endLine": occ.end_lineno,
                                    "column": occ.col_offset,
                                    "endColumn": occ.end_col_offset,
                                    "call_string": call_string,
                                }
                                for occ in occurrences
                            ],
                            "additionalInfo": {
                                "repetitions": len(occurrences),
                            },
                        }
                        results.append(smell)

        return results
