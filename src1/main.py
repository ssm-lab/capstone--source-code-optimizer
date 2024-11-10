import os

from utils.outputs_config import save_json_files, copy_file_to_output

from measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from analyzers.pylint_analyzer import PylintAnalyzer
from utils.refactorer_factory import RefactorerFactory
from utils.logger import Logger

DIRNAME = os.path.dirname(__file__)


def main():
    # Path to the file to be analyzed
    TEST_FILE = os.path.abspath(
        os.path.join(DIRNAME, "../tests/input/ineffcient_code_example_2.py")
    )

    # Set up logging
    LOG_FILE = os.path.join(DIRNAME, "outputs/log.txt")
    logger = Logger(LOG_FILE)

    # Log start of emissions capture
    logger.log(
        "#####################################################################################################"
    )
    logger.log(
        "                                    CAPTURE INITIAL EMISSIONS                                        "
    )
    logger.log(
        "#####################################################################################################"
    )

    # Measure energy with CodeCarbonEnergyMeter
    codecarbon_energy_meter = CodeCarbonEnergyMeter(TEST_FILE, logger)
    codecarbon_energy_meter.measure_energy()
    initial_emissions = codecarbon_energy_meter.emissions  # Get initial emission
    initial_emissions_data = (
        codecarbon_energy_meter.emissions_data
    )  # Get initial emission data

    # Save initial emission data
    save_json_files("initial_emissions_data.txt", initial_emissions_data, logger)
    logger.log(f"Initial Emissions: {initial_emissions} kg CO2")
    logger.log(
        "#####################################################################################################\n\n"
    )

    # Log start of code smells capture
    logger.log(
        "#####################################################################################################"
    )
    logger.log(
        "                                         CAPTURE CODE SMELLS                                         "
    )
    logger.log(
        "#####################################################################################################"
    )

    # Anaylze code smells with PylintAnalyzer
    pylint_analyzer = PylintAnalyzer(TEST_FILE, logger)
    pylint_analyzer.analyze()  # analyze all smells

    # Save code smells
    save_json_files(
        "all_pylint_smells.json", pylint_analyzer.smells_data, logger
    )

    pylint_analyzer.configure_smells()  # get all configured smells

    # Save code smells
    save_json_files(
        "all_configured_pylint_smells.json", pylint_analyzer.smells_data, logger
    )
    logger.log(f"Refactorable code smells: {len(pylint_analyzer.smells_data)}")
    logger.log(
        "#####################################################################################################\n\n"
    )
    
    # Log start of refactoring codes
    logger.log(
        "#####################################################################################################"
    )
    logger.log(
        "                                        REFACTOR CODE SMELLS                                         "
    )
    logger.log(
        "#####################################################################################################"
    )

    # Refactor code smells
    copy_file_to_output(TEST_FILE, "refactored-test-case.py")

    for pylint_smell in pylint_analyzer.smells_data:
        refactoring_class = RefactorerFactory.build_refactorer_class(pylint_smell["message-id"],logger)
        if refactoring_class:
            refactoring_class.refactor(TEST_FILE, pylint_smell, initial_emissions)
        else:
            logger.log(
                f"Refactoring for smell {pylint_smell['symbol']} is not implemented.\n"
            )
    logger.log(
        "#####################################################################################################\n\n"
    )

    # Log start of emissions capture
    logger.log(
        "#####################################################################################################"
    )
    logger.log(
        "                                    CAPTURE FINAL EMISSIONS                                        "
    )
    logger.log(
        "#####################################################################################################"
    )

    # Measure energy with CodeCarbonEnergyMeter
    codecarbon_energy_meter = CodeCarbonEnergyMeter(TEST_FILE, logger)
    codecarbon_energy_meter.measure_energy()  # Measure emissions
    final_emission = codecarbon_energy_meter.emissions  # Get final emission
    final_emission_data = (
        codecarbon_energy_meter.emissions_data
    )  # Get final emission data

    # Save final emission data
    save_json_files("final_emissions_data.txt", final_emission_data, logger)
    logger.log(f"Final Emissions: {final_emission} kg CO2")
    logger.log(
        "#####################################################################################################\n\n"
    )

    # The emissions from codecarbon are so inconsistent that this could be a possibility :(
    if final_emission >= initial_emissions:
        logger.log(
            "Final emissions are greater than initial emissions; we are going to fail"
        )
    else:
        logger.log(f"Saved {initial_emissions - final_emission} kg CO2")


if __name__ == "__main__":
    main()
