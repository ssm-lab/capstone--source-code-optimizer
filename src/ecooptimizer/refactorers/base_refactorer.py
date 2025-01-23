# refactorers/base_refactor.py

from abc import ABC, abstractmethod
import logging
from pathlib import Path

from ..measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from ..data_wrappers.smell import Smell


class BaseRefactorer(ABC):
    def __init__(self, output_dir: Path):
        """
        Base class for refactoring specific code smells.

        :param logger: Logger instance to handle log messages.
        """
        self.temp_dir = (output_dir / "refactored_source").resolve()
        self.temp_dir.mkdir(exist_ok=True)

    @abstractmethod
    def refactor(self, file_path: Path, pylint_smell: Smell, overwrite: bool = True):
        """
        Abstract method for refactoring the code smell.
        Each subclass should implement this method.

        :param file_path: Path to the file to be refactored.
        :param pylint_smell: Dictionary containing details of the Pylint smell.
        :param initial_emission: Initial emission value before refactoring.
        """
        pass

    # def validate_refactoring(
    #     self,
    #     temp_file_path: Path,
    #     original_file_path: Path,
    #     initial_emissions: float,
    #     smell_name: str,
    #     refactor_name: str,
    #     smell_line: int,
    # ):
    #     # Measure emissions of the modified code
    #     final_emission = self.measure_energy(temp_file_path)

    #     if not final_emission:
    #         logging.info(
    #             f"Could not measure emissions for '{temp_file_path.name}'. Discarded refactoring."
    #         )
    #     # Check for improvement in emissions
    #     elif self.check_energy_improvement(initial_emissions, final_emission):
    #         # If improved, replace the original file with the modified content

    #         if run_tests() == 0:
    #             logging.info("All test pass! Functionality maintained.")
    #             # temp_file_path.replace(original_file_path)
    #             logging.info(
    #                 f"Refactored '{smell_name}' to '{refactor_name}' on line {smell_line} and saved.\n"
    #             )
    #             return

    #         logging.info("Tests Fail! Discarded refactored changes")

    #     else:
    #         logging.info(
    #             "No emission improvement after refactoring. Discarded refactored changes.\n"
    #         )

    #     # Remove the temporary file if no energy improvement or failing tests
    #     temp_file_path.unlink()

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
