import json
import os

from measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from analyzers.pylint_analyzer import PylintAnalyzer
from utils.output_config import save_json_files, copy_file_to_output
from utils.refactorer_factory import RefactorerFactory
from utils.logger import Logger


def main():
    # Path to the file to be analyzed
    test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src1-tests/ineffcient_code_example_1.py"))

    # Set up logging
    log_file = os.path.join(os.path.dirname(__file__), "outputs/log.txt")
    logger = Logger(log_file)




    # Log start of emissions capture
    logger.log("#####################################################################################################")
    logger.log("                                    CAPTURE INITIAL EMISSIONS                                        ")
    logger.log("#####################################################################################################")

    # Measure energy with CodeCarbonEnergyMeter
    codecarbon_energy_meter = CodeCarbonEnergyMeter(test_file, logger)
    codecarbon_energy_meter.measure_energy()  # Measure emissions
    initial_emission = codecarbon_energy_meter.emissions  # Get initial emission
    initial_emission_data = codecarbon_energy_meter.emissions_data  # Get initial emission data

    # Save initial emission data
    save_json_files("initial_emissions_data.txt", initial_emission_data, logger)
    logger.log(f"Initial Emissions: {initial_emission} kg CO2")
    logger.log("#####################################################################################################\n\n")




    # Log start of code smells capture
    logger.log("#####################################################################################################")
    logger.log("                                         CAPTURE CODE SMELLS                                         ")
    logger.log("#####################################################################################################")
    
    # Anaylze code smells with PylintAnalyzer
    pylint_analyzer = PylintAnalyzer(test_file, logger)
    pylint_analyzer.analyze_smells() # analyze all smells
    detected_pylint_smells = pylint_analyzer.get_configured_smells() # get all configured smells

    # Save code smells
    save_json_files("all_configured_pylint_smells.json", detected_pylint_smells, logger)
    logger.log(f"Refactorable code smells: {len(detected_pylint_smells)}")
    logger.log("#####################################################################################################\n\n")




    # Log start of refactoring codes
    logger.log("#####################################################################################################")
    logger.log("                                        REFACTOR CODE SMELLS                                         ")
    logger.log("#####################################################################################################")

    # Refactor code smells
    test_file_copy = copy_file_to_output(test_file, "refactored-test-case.py")
    emission = initial_emission

    for pylint_smell in detected_pylint_smells:
        refactoring_class = RefactorerFactory.build_refactorer_class(test_file_copy, pylint_smell["message-id"], pylint_smell, emission, logger)

        if refactoring_class:
            refactoring_class.refactor()
            emission = refactoring_class.final_emission
        else:
            logger.log(f"Refactoring for smell {pylint_smell['symbol']} is not implemented.")
    logger.log("#####################################################################################################\n\n")

        


    # Log start of emissions capture
    logger.log("#####################################################################################################")
    logger.log("                                    CAPTURE FINAL EMISSIONS                                        ")
    logger.log("#####################################################################################################")

    # Measure energy with CodeCarbonEnergyMeter
    codecarbon_energy_meter = CodeCarbonEnergyMeter(test_file, logger)
    codecarbon_energy_meter.measure_energy()  # Measure emissions
    final_emission = codecarbon_energy_meter.emissions  # Get final emission
    final_emission_data = codecarbon_energy_meter.emissions_data  # Get final emission data

    # Save final emission data
    save_json_files("final_emissions_data.txt", final_emission_data, logger)
    logger.log(f"Final Emissions: {final_emission} kg CO2")
    logger.log("#####################################################################################################\n\n")




    # The emissions from codecarbon are so inconsistent that this could be a possibility :(
    if final_emission >= initial_emission:
        logger.log(f"Final emissions are greater than initial emissions; we are going to fail")
    else:
        logger.log(f"Saved {initial_emission - final_emission} kg CO2")


if __name__ == "__main__":
    main()
