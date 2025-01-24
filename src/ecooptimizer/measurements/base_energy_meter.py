from abc import ABC, abstractmethod
from pathlib import Path


class BaseEnergyMeter(ABC):
    def __init__(self):
        """
        Base class for energy meters to measure the emissions of a given file.

        :param file_path: Path to the file to measure energy consumption.
        :param logger: Logger instance to handle log messages.
        """
        self.emissions = None

    @abstractmethod
    def measure_energy(self, file_path: Path):
        """
        Abstract method to measure the energy consumption of the specified file.
        Must be implemented by subclasses.
        """
        pass
