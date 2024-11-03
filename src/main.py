from analyzers.pylint_analyzer import PylintAnalyzer


def main():
    """
    Entry point for the refactoring tool.
    - Create an instance of the analyzer.
    - Perform code analysis and print the results.
    """

    # okay so basically this guy gotta call 1) pylint 2) refactoring class for every bug
    path = "/Users/mya/Code/Capstone/capstone--source-code-optimizer/test/inefficent_code_example.py"
    analyzer = PylintAnalyzer(path)
    report = analyzer.analyze()

    print("THIS IS REPORT for our smells:")
    detected_smells = analyzer.filter_for_all_wanted_code_smells(report)
    print(detected_smells)

    for smell in detected_smells:
        refactoring_class = analyzer.code_smells[smell["message-id"]]

        refactoring_class.refactor(smell, path)


if __name__ == "__main__":
    main()
