import io
import json
from io import StringIO
import os
from pylint import run_pylint
from base_analyzer import BaseAnalyzer


class PylintAnalyzer(BaseAnalyzer):
    def __init__(self, code_path: str):
        super().__init__(code_path)
        # We are going to use the codes to identify the smells this is a dict of all of them
        self.code_smells = {
            "R0902": "Large Class",  # Too many instance attributes
            "R0913": "Long Parameter List",  # Too many arguments
            "R0915": "Long Method",  # Too many statements
            "C0200": "Complex List Comprehension",  # Loop can be simplified
            "C0103": "Invalid Naming Convention",  # Non-standard names
            
            # Add other pylint codes as needed
        }

    def analyze(self):
        """
        Runs pylint on the specified Python file and returns the output as a list of dictionaries.
        Each dictionary contains information about a code smell or warning identified by pylint.

        :param file_path: The path to the Python file to be analyzed.
        :return: A list of dictionaries with pylint messages.
        """
        # Capture pylint output into a string stream
        output_stream = io.StringIO()

        # Run pylint
        Run(["--output-format=json", self.code_path])

        # Retrieve and parse output as JSON
        output = output_stream.getvalue()
        try:
            pylint_results = json.loads(output)
        except json.JSONDecodeError:
            print("Error: Could not decode pylint output")
            pylint_results = []

        return pylint_results



from pylint.lint import Run

# Example usage
if __name__ == "__main__":

    print(os.path.abspath("../test/inefficent_code_example.py"))

    # FOR SOME REASON THIS ISNT WORKING UNLESS THE PATH IS ABSOLUTE
    # this is probably because its executing from the location of the interpreter
    # weird thing is it breaks when you use abs path instead... uhhh idk what to do here rn ...

    analyzer = PylintAnalyzer(
        "/Users/mya/Code/Capstone/capstone--source-code-optimizer/test/inefficent_code_example.py"
    )
    report = analyzer.analyze()

    print("THIS IS REPORT:")
    print(report)
