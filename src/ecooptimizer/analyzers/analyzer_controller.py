import json
from pathlib import Path
from .pylint_analyzer import PylintAnalyzer
from .ast_analyzer import ASTAnalyzer
from configs.analyzers_config import EXTRA_PYLINT_OPTIONS, EXTRA_AST_OPTIONS


class AnalyzerController:
    """
    Controller to coordinate the execution of various analyzers and compile the results.
    """

    def __init__(self):
        """
        Initializes the AnalyzerController with no arguments.
        This class is responsible for managing and executing analyzers.
        """
        pass

    def run_analysis(self, file_path: Path, output_path: Path):
        """
        Executes all configured analyzers on the specified file and saves the results.

        Parameters:
            file_path (Path): The path of the file to analyze.
            output_path (Path): The path to save the analysis results as a JSON file.
        """
        self.smells_data = []  # Initialize a list to store detected smells
        self.file_path = file_path
        self.output_path = output_path

        # Run the Pylint analyzer if there are extra options configured
        if EXTRA_PYLINT_OPTIONS:
            pylint_analyzer = PylintAnalyzer(file_path, EXTRA_PYLINT_OPTIONS)
            pylint_analyzer.analyze()
            self.smells_data.extend(pylint_analyzer.smells_data)

        # Run the AST analyzer if there are extra options configured
        if EXTRA_AST_OPTIONS:
            ast_analyzer = ASTAnalyzer(file_path, EXTRA_AST_OPTIONS)
            ast_analyzer.analyze()
            self.smells_data.extend(ast_analyzer.smells_data)

        # Save the combined analysis results to a JSON file
        self._write_to_json(self.smells_data, output_path)

    def _write_to_json(self, smells_data: list[object], output_path: Path):
        """
        Writes the detected smells data to a JSON file.

        Parameters:
            smells_data (list[object]): List of detected smells.
            output_path (Path): The path to save the JSON file.

        Raises:
            Exception: If writing to the JSON file fails.
        """
        try:
            with output_path.open("w") as output_file:
                json.dump(smells_data, output_file, indent=4)
            print(f"Analysis results saved to {output_path}")
        except Exception as e:
            print(f"Failed to write results to JSON: {e}")
