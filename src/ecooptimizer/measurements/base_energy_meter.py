from abc import ABC, abstractmethod
from pathlib import Path


class BaseEnergyMeter(ABC):
    """
    Abstract base class for energy meters that measure the emissions of a given file.
    """

    def __init__(self):
        """
        Initializes the base energy meter with an emissions attribute.
        """
        self.emissions = None

    @abstractmethod
    def measure_energy(self, file_path: Path):
        """
        Measures the energy consumption of the specified file.

        Args:
            file_path (Path): Path to the file to measure energy consumption.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        pass
