import os

from analyzers.pylint_analyzer import PylintAnalyzer
from measurement.code_carbon_meter import CarbonAnalyzer
from utils.factory import RefactorerFactory

dirname = os.path.dirname(__file__)

def main():
    """
    Entry point for the refactoring tool.
    - Create an instance of the analyzer.
    - Perform code analysis and print the results.
    """

    # okay so basically this guy gotta call 1) pylint 2) refactoring class for every bug
    TEST_FILE_PATH = os.path.join(dirname, "../test/inefficent_code_example.py")
    INITIAL_REPORT_FILE_PATH = os.path.join(dirname, "output/initial_carbon_report.csv")

    carbon_analyzer = CarbonAnalyzer(TEST_FILE_PATH)
    carbon_analyzer.run_and_measure()
    carbon_analyzer.save_report(INITIAL_REPORT_FILE_PATH)
    
    analyzer = PylintAnalyzer(TEST_FILE_PATH)
    report = analyzer.analyze()

    detected_smells = analyzer.filter_for_all_wanted_code_smells(report["messages"])

    for smell in detected_smells:
        smell_id: str = smell["messageId"]

        print("Refactoring ", smell_id)
        refactoring_class = RefactorerFactory.build(smell_id, TEST_FILE_PATH)
        refactoring_class.refactor()


if __name__ == "__main__":
    main()
