# FULLY CHATGPT - I only wanted to add this in so we have an idea how to detect smells pylint can't

import ast
from .base_analyzer import Analyzer

class TernaryExpressionAnalyzer(Analyzer):
    def __init__(self, file_path, max_length=50):
        super().__init__(file_path)
        self.max_length = max_length

    def analyze(self):
        """
        Reads the file and analyzes it to detect long ternary expressions.
        """
        if not self.validate_file():
            print(f"File not found: {self.file_path}")
            return

        print(f"Running ternary expression analysis on {self.file_path}")

        try:
            code = self.read_code_from_file()
            self.report_data = self.detect_long_ternary_expressions(code)
            print("Ternary expression analysis completed.")
        except FileNotFoundError:
            print(f"File not found: {self.file_path}")
        except IOError as e:
            print(f"Error reading file {self.file_path}: {e}")

    def read_code_from_file(self):
        """
        Reads and returns the code from the specified file path.

        :return: Source code as a string.
        """
        with open(self.file_path, "r") as file:
            return file.read()

    def detect_long_ternary_expressions(self, code):
        """
        Detects ternary expressions in the code that exceed the specified max_length.

        :param code: The source code to analyze.
        :return: List of detected long ternary expressions with line numbers and expression length.
        """
        tree = ast.parse(code)
        long_expressions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.IfExp):  # Ternary expression node
                expression_source = ast.get_source_segment(code, node)
                expression_length = len(expression_source) if expression_source else 0
                if expression_length > self.max_length:
                    long_expressions.append({
                        "line": node.lineno,
                        "length": expression_length,
                        "expression": expression_source
                    })

        return long_expressions

    def filter_expressions_by_length(self, min_length):
        """
        Filters the report data to retrieve only the expressions exceeding a specified length.

        :param min_length: Minimum length of expressions to filter by.
        :return: List of detected ternary expressions matching the specified length criteria.
        """
        return [expr for expr in self.report_data if expr["length"] >= min_length]
