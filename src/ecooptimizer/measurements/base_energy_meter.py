"""Abstract base class for energy measurement implementations."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseEnergyMeter(ABC):
    """Abstract base class for measuring code energy consumption.

    Provides the interface for concrete energy measurement implementations.
    """

    def __init__(self):
        """Initializes the energy meter with empty emissions."""
        self.emissions = None

    @abstractmethod
    def measure_energy(self, file_path: Path) -> None:
        """Measures energy consumption of a code file.

        Args:
            file_path: Path to the file to measure

        Note:
            Must be implemented by concrete subclasses
        """
        pass
