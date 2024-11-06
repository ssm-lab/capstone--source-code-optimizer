import ast
import os

from analyzers.pylint_analyzer import PylintAnalyzer
from utils.factory import RefactorerFactory
from utils.code_smells import CodeSmells
from utils import ast_parser

dirname = os.path.dirname(__file__)

def main():
    """
    Entry point for the refactoring tool.
    - Create an instance of the analyzer.
    - Perform code analysis and print the results.
    """

    # okay so basically this guy gotta call 1) pylint 2) refactoring class for every bug
    FILE_PATH = os.path.join(dirname, "../test/inefficent_code_example.py")
    
    analyzer = PylintAnalyzer(FILE_PATH)
    report = analyzer.analyze()

    filtered_report = analyzer.filter_for_all_wanted_code_smells(report["messages"])
    detected_smells = filtered_report[0]
    # statistics = filtered_report[1]

    for smell in detected_smells:
        smell_id = smell["messageId"]

        if smell_id == CodeSmells.LINE_TOO_LONG.value:
            root_node = ast_parser.parse_line(FILE_PATH, smell["line"])

            if root_node is None:
                continue

            smell_id = CodeSmells.LONG_TERN_EXPR

            # for node in ast.walk(root_node):
            #     print("Body: ", node["body"])
            #     for expr in ast.walk(node.body[0]):
            #         if isinstance(expr, ast.IfExp):
            #             smell_id = CodeSmells.LONG_TERN_EXPR

        print("Refactoring ", smell_id)
        refactoring_class = RefactorerFactory.build(smell_id, FILE_PATH)
        refactoring_class.refactor()


if __name__ == "__main__":
    main()
