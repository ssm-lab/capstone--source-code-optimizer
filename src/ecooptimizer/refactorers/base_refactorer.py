# refactorers/base_refactor.py

from abc import ABC, abstractmethod
import logging
from pathlib import Path
from ecooptimizer.measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter

from ecooptimizer.data_wrappers.smell import Smell


class BaseRefactorer(ABC):
    def __init__(self):
        """
        Base class for refactoring specific code smells.

        :param logger: Logger instance to handle log messages.
        """
        self.temp_dir = (
            Path(__file__) / Path("../../../../../../outputs/refactored_source")
        ).resolve()
        self.temp_dir.mkdir(exist_ok=True)

    @abstractmethod
    def refactor(self, file_path: Path, pylint_smell: Smell, initial_emissions: float):
        """
        Abstract method for refactoring the code smell.
        Each subclass should implement this method.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell.
        :param initial_emission: Initial emission value before refactoring.
        """
        pass

    def measure_energy(self, file_path: Path):
        """
        Method for measuring the energy after refactoring.
        """
        codecarbon_energy_meter = CodeCarbonEnergyMeter(file_path)
        codecarbon_energy_meter.measure_energy()  # measure emissions
        emissions = codecarbon_energy_meter.emissions  # get emission

        if not emissions:
            return None

        # Log the measured emissions
        logging.info(f"Measured emissions for '{file_path.name}': {emissions}")

        return emissions

    def check_energy_improvement(self, initial_emissions: float, final_emissions: float):
        """
        Checks if the refactoring has reduced energy consumption.

        :return: True if the final emission is lower than the initial emission, indicating improvement;
                 False otherwise.
        """
        improved = final_emissions and (final_emissions < initial_emissions)
        logging.info(
            f"Initial Emissions: {initial_emissions} kg CO2. Final Emissions: {final_emissions} kg CO2."
        )
        return improved


print(__file__)
