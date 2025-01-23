import ast
import logging
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from .utils.ast_parser import parse_file
from .utils.outputs_config import OutputConfig

from .measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from .analyzers.pylint_analyzer import PylintAnalyzer
from .utils.refactorer_factory import RefactorerFactory
from .testing.test_runner import TestRunner

# Path of current directory
DIRNAME = Path(__file__).parent
# Path to output folder
OUTPUT_DIR = (DIRNAME / Path("../../outputs")).resolve()
# Path to log file
LOG_FILE = OUTPUT_DIR / Path("log.log")
# Path to the file to be analyzed
SAMPLE_PROJ_DIR = (DIRNAME / Path("../../tests/input/project_string_concat")).resolve()
SOURCE = SAMPLE_PROJ_DIR / "main.py"
TEST_FILE = SAMPLE_PROJ_DIR / "test_main.py"


def main():
    output_config = OutputConfig(OUTPUT_DIR)

    # Set up logging
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="w",
        level=logging.INFO,
        format="[ecooptimizer %(levelname)s @ %(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    SOURCE_CODE = parse_file(SOURCE)
    output_config.save_file(Path("source_ast.txt"), ast.dump(SOURCE_CODE, indent=2), "w")

    if not SOURCE.is_file():
        logging.error(f"Cannot find source code file '{SOURCE}'. Exiting...")
        exit(1)

    # Check that tests pass originally
    test_runner = TestRunner("pytest", SAMPLE_PROJ_DIR)
    if not test_runner.retained_functionality():
        logging.error("Provided test suite fails with original source code.")
        exit(1)

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
    codecarbon_energy_meter = CodeCarbonEnergyMeter(SOURCE)
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
    pylint_analyzer = PylintAnalyzer(SOURCE, SOURCE_CODE)
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

    with TemporaryDirectory() as temp_dir:
        project_copy = Path(temp_dir) / SAMPLE_PROJ_DIR.name

        source_copy = project_copy / SOURCE.name

        shutil.copytree(SAMPLE_PROJ_DIR, project_copy)

        # Refactor code smells
        backup_copy = output_config.copy_file_to_output(source_copy, "refactored-test-case.py")

        for pylint_smell in pylint_analyzer.smells_data:
            refactoring_class = RefactorerFactory.build_refactorer_class(
                pylint_smell["messageId"], OUTPUT_DIR
            )
            if refactoring_class:
                refactoring_class.refactor(source_copy, pylint_smell)

                if not TestRunner("pytest", Path(temp_dir)).retained_functionality():
                    logging.info("Functionality not maintained. Discarding refactoring.\n")
            else:
                logging.info(
                    f"Refactoring for smell {pylint_smell['symbol']} is not implemented.\n"
                )

            # Revert temp
            shutil.copy(backup_copy, source_copy)

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
    codecarbon_energy_meter = CodeCarbonEnergyMeter(SOURCE)
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
