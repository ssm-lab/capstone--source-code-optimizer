import os

class Analyzer:
    """
    Base class for different types of analyzers.
    """
    def __init__(self, file_path):
        """
        Initializes the analyzer with a file path.

        :param file_path: Path to the file to be analyzed.
        """
        self.file_path = file_path
        self.report_data = []

    def validate_file(self):
        """
        Checks if the file path exists and is a file.
        
        :return: Boolean indicating file validity.
        """
        return os.path.isfile(self.file_path)

    def analyze(self):
        """
        Abstract method to be implemented by subclasses to perform analysis.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_all_detected_smells(self):
        """
        Retrieves all detected smells from the report data.

        :return: List of all detected code smells.
        """
        return self.report_data
