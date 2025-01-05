import logging
from pathlib import Path

from .utils.ast_parser import parse_file
from .utils.outputs_config import OutputConfig

from .measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from .analyzers.pylint_analyzer import PylintAnalyzer
from .utils.refactorer_factory import RefactorerFactory

# Path of current directory
DIRNAME = Path(__file__).parent
print("hello: ", DIRNAME)
# Path to output folder
OUTPUT_DIR = (DIRNAME / Path("../../outputs")).resolve()
# Path to log file
LOG_FILE = OUTPUT_DIR / Path("log.log")
# Path to the file to be analyzed
TEST_FILE = (DIRNAME / Path("../../tests/input/car_stuff.py")).resolve()


def main():
    output_config = OutputConfig(OUTPUT_DIR)

    # Set up logging
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="w",
        level=logging.DEBUG,
        format="[ecooptimizer %(levelname)s @ %(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    SOURCE_CODE = parse_file(TEST_FILE)

    if not TEST_FILE.is_file():
        logging.error(f"Cannot find source code file '{TEST_FILE}'. Exiting...")

    # Log start of emissions capture
    logging.info(
        "#####################################################################################################"
    )
    logging.info(
        "                                    CAPTURE INITIAL EMISSIONS                                        "
    )
    logging.info(
        "#####################################################################################################"
    )

    # Measure energy with CodeCarbonEnergyMeter
    codecarbon_energy_meter = CodeCarbonEnergyMeter(TEST_FILE)
    codecarbon_energy_meter.measure_energy()
    initial_emissions = codecarbon_energy_meter.emissions  # Get initial emission

    if not initial_emissions:
        logging.error("Could not retrieve initial emissions. Ending Task.")
        exit(0)

    initial_emissions_data = codecarbon_energy_meter.emissions_data  # Get initial emission data

    if initial_emissions_data:
        # Save initial emission data
        output_config.save_json_files(Path("initial_emissions_data.txt"), initial_emissions_data)
    else:
        logging.error("Could not retrieve emissions data. No save file created.")

    logging.info(f"Initial Emissions: {initial_emissions} kg CO2")
    logging.info(
        "#####################################################################################################\n\n"
    )

    # Log start of code smells capture
    logging.info(
        "#####################################################################################################"
    )
    logging.info(
        "                                         CAPTURE CODE SMELLS                                         "
    )
    logging.info(
        "#####################################################################################################"
    )

    # Anaylze code smells with PylintAnalyzer
    pylint_analyzer = PylintAnalyzer(TEST_FILE, SOURCE_CODE)
    pylint_analyzer.analyze()  # analyze all smells

    # Save code smells
    output_config.save_json_files(Path("all_pylint_smells.json"), pylint_analyzer.smells_data)

    pylint_analyzer.configure_smells()  # get all configured smells

    # Save code smells
    output_config.save_json_files(
        Path("all_configured_pylint_smells.json"), pylint_analyzer.smells_data
    )
    logging.info(f"Refactorable code smells: {len(pylint_analyzer.smells_data)}")
    logging.info(
        "#####################################################################################################\n\n"
    )

    # Log start of refactoring codes
    logging.info(
        "#####################################################################################################"
    )
    logging.info(
        "                                        REFACTOR CODE SMELLS                                         "
    )
    logging.info(
        "#####################################################################################################"
    )

    # Refactor code smells
    output_config.copy_file_to_output(TEST_FILE, "refactored-test-case.py")

    for pylint_smell in pylint_analyzer.smells_data:
        refactoring_class = RefactorerFactory.build_refactorer_class(pylint_smell["messageId"])
        if refactoring_class:
            refactoring_class.refactor(TEST_FILE, pylint_smell, initial_emissions)
        else:
            logging.info(f"Refactoring for smell {pylint_smell['symbol']} is not implemented.\n")
    logging.info(
        "#####################################################################################################\n\n"
    )

    return

    # Log start of emissions capture
    logging.info(
        "#####################################################################################################"
    )
    logging.info(
        "                                    CAPTURE FINAL EMISSIONS                                        "
    )
    logging.info(
        "#####################################################################################################"
    )

    # Measure energy with CodeCarbonEnergyMeter
    codecarbon_energy_meter = CodeCarbonEnergyMeter(TEST_FILE)
    codecarbon_energy_meter.measure_energy()  # Measure emissions
    final_emission = codecarbon_energy_meter.emissions  # Get final emission
    final_emission_data = codecarbon_energy_meter.emissions_data  # Get final emission data

    # Save final emission data
    output_config.save_json_files("final_emissions_data.txt", final_emission_data)
    logging.info(f"Final Emissions: {final_emission} kg CO2")
    logging.info(
        "#####################################################################################################\n\n"
    )

    # The emissions from codecarbon are so inconsistent that this could be a possibility :(
    if final_emission >= initial_emissions:
        logging.info(
            "Final emissions are greater than initial emissions. No optimal refactorings found."
        )
    else:
        logging.info(f"Saved {initial_emissions - final_emission} kg CO2")


if __name__ == "__main__":
    main()
