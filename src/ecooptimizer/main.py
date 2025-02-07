import ast
import logging
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory, mkdtemp  # noqa: F401

from .api.main import RefactoredData


from .measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter

from .analyzers.analyzer_controller import AnalyzerController

from .refactorers.refactorer_controller import RefactorerController

from . import (
    OUTPUT_MANAGER,
    SAMPLE_PROJ_DIR,
    SOURCE,
    OUTPUT_DIR,
)

# FILE CONFIGURATION IN __init__.py !!!


def main():
    # Save ast
    OUTPUT_MANAGER.save_file(
        "source_ast.txt", ast.dump(ast.parse(SOURCE.read_text()), indent=4), "w"
    )

    # Measure initial energy
    energy_meter = CodeCarbonEnergyMeter()
    energy_meter.measure_energy(Path(SOURCE))
    initial_emissions = 1000

    if not initial_emissions:
        logging.error("Could not retrieve initial emissions. Exiting.")
        exit(1)

    analyzer_controller = AnalyzerController()
    smells_data = analyzer_controller.run_analysis(SOURCE)
    OUTPUT_MANAGER.save_json_files(
        "code_smells.json", [smell.model_dump() for smell in smells_data]
    )

    OUTPUT_MANAGER.copy_file_to_output(SOURCE, "refactored-test-case.py")
    refactorer_controller = RefactorerController(OUTPUT_DIR)
    output_paths = []

    for smell in smells_data:
        if smell.messageId == "R0913" and smell.occurences[0].line == 83:
            # Use the line below and comment out "with TemporaryDirectory()" if you want to see the refactored code
            # It basically copies the source directory into a temp dir that you can find in your systems TEMP folder
            # It varies per OS. The location of the folder can be found in the 'refactored-data.json' file in outputs.
            # If you use the other line know that you will have to manually delete the temp dir after running the
            # code. It will NOT auto delete which, hence allowing you to see the refactoring results

            tempDir = mkdtemp(
                prefix="ecooptimizer-"
            )  # < UNCOMMENT THIS LINE and shift code under to the left

            # with TemporaryDirectory() as tempDir:  # COMMENT OUT THIS ONE
            source_copy = Path(tempDir) / SAMPLE_PROJ_DIR.name
            target_file_copy = Path(str(SOURCE).replace(str(SAMPLE_PROJ_DIR), str(source_copy), 1))

            # source_copy = project_copy / SOURCE.name

            shutil.copytree(SAMPLE_PROJ_DIR, source_copy)

            try:
                modified_files: list[Path] = refactorer_controller.run_refactorer(
                    target_file_copy, source_copy, smell, overwrite=False
                )
            except NotImplementedError as e:
                print(e)
                continue

            energy_meter.measure_energy(target_file_copy)
            final_emissions = 1

            if not final_emissions:
                logging.error("Could not retrieve final emissions. Discarding refactoring.")
                print("Refactoring Failed.\n")

            elif final_emissions >= initial_emissions:
                logging.info("No measured energy savings. Discarding refactoring.\n")
                print("Refactoring Failed.\n")

            else:
                logging.info("Energy saved!")
                logging.info(
                    f"Initial emissions: {initial_emissions} | Final emissions: {final_emissions}"
                )

                # if not TestRunner("pytest", Path(tempDir)).retained_functionality():
                #     logging.info("Functionality not maintained. Discarding refactoring.\n")
                #     print("Refactoring Failed.\n")

                # else:
                logging.info("Functionality maintained! Retaining refactored file.\n")
                print("Refactoring Succesful!\n")

                refactor_data = RefactoredData(
                    tempDir=tempDir,
                    targetFile=str(target_file_copy).replace(
                        str(source_copy), str(SAMPLE_PROJ_DIR), 1
                    ),
                    energySaved=(final_emissions - initial_emissions),
                    refactoredFiles=[str(file) for file in modified_files],
                )

                output_paths = refactor_data.refactoredFiles

                # In reality the original code will now be overwritten but thats too much work

                OUTPUT_MANAGER.save_json_files("refactoring-data.json", refactor_data.model_dump())  # type: ignore
            print(output_paths)


if __name__ == "__main__":
    main()
