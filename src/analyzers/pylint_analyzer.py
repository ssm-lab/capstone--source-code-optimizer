import subprocess
import json
from analyzers.base_analyzer import BaseAnalyzer

class PylintAnalyzer(BaseAnalyzer):
    def __init__(self, code_path: str):
        super().__init__(code_path)
        self.code_smells = {
            "R0902": "Large Class",       # Too many instance attributes
            "R0913": "Long Parameter List",  # Too many arguments
            "R0915": "Long Method",       # Too many statements
            "C0200": "Complex List Comprehension",  # Loop can be simplified
            "C0103": "Invalid Naming Convention",  # Non-standard names
            # Add other pylint codes as needed
        }

    def analyze(self):
        """
        Runs Pylint on the specified code path and returns a report of code smells.
        """
        pylint_command = [
            "pylint", "--output-format=json", self.code_path
        ]
        
        try:
            result = subprocess.run(pylint_command, capture_output=True, text=True, check=True)
            pylint_output = result.stdout
            report = self._parse_pylint_output(pylint_output)
            return report
        except subprocess.CalledProcessError as e:
            print("Pylint analysis failed:", e)
            return {}
        except FileNotFoundError:
            print("Pylint is not installed or not found in PATH.")
            return {}
        except json.JSONDecodeError:
            print("Failed to parse pylint output. Check if pylint output is in JSON format.")
            return {}

    def _parse_pylint_output(self, output: str):
        """
        Parses the Pylint JSON output to identify specific code smells.
        """
        try:
            pylint_results = json.loads(output)
        except json.JSONDecodeError:
            print("Error: Failed to parse pylint output")
            return []
        
        code_smell_report = []

        for entry in pylint_results:
            message_id = entry.get("message-id")
            if message_id in self.code_smells:
                code_smell_report.append({
                    "type": self.code_smells[message_id],
                    "message": entry.get("message"),
                    "line": entry.get("line"),
                    "column": entry.get("column"),
                    "path": entry.get("path")
                })
        
        return code_smell_report

# Example usage
if __name__ == "__main__":
    analyzer = PylintAnalyzer("your_file.py")
    report = analyzer.analyze()
    for issue in report:
        print(f"{issue['type']} at {issue['path']}:{issue['line']}:{issue['column']} - {issue['message']}")
