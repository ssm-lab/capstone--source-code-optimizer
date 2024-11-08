import ast
from utils.ast_parser import parse_line
from utils.analyzers_config import AllPylintSmells

class TernaryExpressionPylintAnalyzer:
    def __init__(self, file_path, smells_data):
        """
        Initializes with smells data from PylintAnalyzer to find long ternary 
        expressions.
        
        :param file_path: Path to file used by PylintAnalyzer.
        :param smells_data: List of smells from PylintAnalyzer.
        """
        self.file_path = file_path
        self.smells_data = smells_data

    def detect_long_ternary_expressions(self):
        """
        Processes long lines to identify ternary expressions.
        
        :return: List of smells with updated ternary expression detection message IDs.
        """
        for smell in self.smells_data:
            if smell.get("message-id") == AllPylintSmells.LINE_TOO_LONG.value:
                root_node = parse_line(self.file_path, smell["line"])

                if root_node is None:
                    continue

                for node in ast.walk(root_node):
                    if isinstance(node, ast.IfExp):  # Ternary expression node
                        smell["message-id"] = AllPylintSmells.LONG_TERN_EXPR.value
                        break

        return self.smells_data
