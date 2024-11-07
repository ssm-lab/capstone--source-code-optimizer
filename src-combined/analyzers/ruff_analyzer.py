import subprocess

from os.path import abspath, dirname
import sys

# Sets src as absolute path, everything needs to be relative to src folder
REFACTOR_DIR = dirname(abspath(__file__))
sys.path.append(dirname(REFACTOR_DIR))

from analyzers.base_analyzer import BaseAnalyzer

class RuffAnalyzer(BaseAnalyzer):
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
        # Base command to run Ruff
        command = ["ruff", "check", "--select", "ALL", self.code_path]
        
        # # Add config file option if specified
        # if config_file:
        #     command.extend(["--config", config_file])
        
        try:
            # Run the command and capture output
            result = subprocess.run(command, text=True, capture_output=True, check=True)
            
            # Print the output from Ruff
            with open("output/ruff.txt", "a+") as f:
                f.write(result.stdout)
            # print("Ruff output:")
            # print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            # If Ruff fails (e.g., lint errors), capture and print error output
            print("Ruff encountered issues:")
            print(e.stdout)  # Ruff's linting output
            print(e.stderr)  # Any additional error information
            sys.exit(1)  # Exit with a non-zero status if Ruff fails

    # def filter_for_all_wanted_code_smells(self, pylint_results):
    #     statistics = {}
    #     report = []
    #     filtered_results = []

    #     for error in pylint_results:
    #         if error["messageId"] in CodeSmells.list():
    #             statistics[error["messageId"]] = True
    #             filtered_results.append(error)
        
    #     report.append(filtered_results)
    #     report.append(statistics)

    #     with open("src/output/report.txt", "w+") as f:
    #         print(json.dumps(report, indent=2), file=f)

    #     return report

    # def filter_for_one_code_smell(self, pylint_results, code):
    #     filtered_results = []
    #     for error in pylint_results:
    #         if error["messageId"] == code:
    #             filtered_results.append(error)

    #     return filtered_results

# Example usage
if __name__ == "__main__":

    FILE_PATH = abspath("test/inefficent_code_example.py")
    OUTPUT_FILE = abspath("src/output/ruff.txt")

    analyzer = RuffAnalyzer(FILE_PATH)

    # print("THIS IS REPORT for our smells:")
    analyzer.analyze()

    # print(report)

    # with open("src/output/ast.txt", "w+") as f:
    #     print(parse_file(FILE_PATH), file=f)

    # filtered_results = analyzer.filter_for_one_code_smell(report["messages"], "C0301")


    # with open(FILE_PATH, "r") as f:
    #     file_lines = f.readlines()

    # for smell in filtered_results:
    #     with open("src/output/ast_lines.txt", "a+") as f:
    #         print("Parsing line ", smell["line"], file=f)
    #         print(parse_line(file_lines, smell["line"]), end="\n", file=f)
        


    
