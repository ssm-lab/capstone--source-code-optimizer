# refactorers/base_refactor.py

from abc import ABC, abstractmethod
import os
from measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter

class BaseRefactorer(ABC):
    def __init__(self, logger):
        """
        Base class for refactoring specific code smells.

        :param logger: Logger instance to handle log messages.
        """
        
        self.logger = logger  # Store the mandatory logger instance

    @abstractmethod
    def refactor(self, file_path: str, pylint_smell: object, initial_emissions: float):
        """
        Abstract method for refactoring the code smell.
        Each subclass should implement this method.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell.
        :param initial_emission: Initial emission value before refactoring.
        """
        pass

    def measure_energy(self, file_path: str) -> float:
        """
        Method for measuring the energy after refactoring.
        """
        codecarbon_energy_meter = CodeCarbonEnergyMeter(file_path, self.logger)
        codecarbon_energy_meter.measure_energy()  # measure emissions
        emissions = codecarbon_energy_meter.emissions  # get emission

        # Log the measured emissions
        self.logger.log(f"Measured emissions for '{os.path.basename(file_path)}': {emissions}")

        return emissions

    def check_energy_improvement(self, initial_emissions: float, final_emissions: float):
        """
        Checks if the refactoring has reduced energy consumption.

        :return: True if the final emission is lower than the initial emission, indicating improvement;
                 False otherwise.
        """
        improved = final_emissions and (final_emissions < initial_emissions)
        self.logger.log(f"Initial Emissions: {initial_emissions} kg CO2. Final Emissions: {final_emissions} kg CO2.")
        return improved
