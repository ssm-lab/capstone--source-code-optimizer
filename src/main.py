from analyzers.pylint_analyzer import PylintAnalyzer

def main():
    """
    Entry point for the refactoring tool.
    - Create an instance of the analyzer.
    - Perform code analysis and print the results.
    """
    code_path = "path/to/your/code"  # Path to the code to analyze
    analyzer = PylintAnalyzer(code_path)
    report = analyzer.analyze()  # Analyze the code
    print(report)  # Print the analysis report

if __name__ == "__main__":
    main()
