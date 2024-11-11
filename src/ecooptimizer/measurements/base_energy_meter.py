from abc import ABC, abstractmethod
import os
from utils.logger import Logger

class BaseEnergyMeter(ABC):
    def __init__(self, file_path: str, logger: Logger):
        """
        Base class for energy meters to measure the emissions of a given file.
        
        :param file_path: Path to the file to measure energy consumption.
        :param logger: Logger instance to handle log messages.
        """
        self.file_path = file_path
        self.emissions = None
        self.logger = logger  # Use logger instance

    def validate_file(self):
        """
        Validates that the specified file path exists and is a file.
        
        :return: Boolean indicating the validity of the file path.
        """
        is_valid = os.path.isfile(self.file_path)
        if not is_valid:
            self.logger.log(f"File not found: {self.file_path}")
        return is_valid

    @abstractmethod
    def measure_energy(self):
        """
        Abstract method to measure the energy consumption of the specified file.
        Must be implemented by subclasses.
        """
        pass
