import logging
from pathlib import Path

from .analyzers.analyzer_controller import AnalyzerController

from .utils.outputs_config import OutputConfig

from .refactorers.refactorer_controller import RefactorerController

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
    # Set up logging
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="w",
        level=logging.INFO,
        format="[ecooptimizer %(levelname)s @ %(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    output_config = OutputConfig(OUTPUT_DIR)

    analyzer_controller = AnalyzerController()
    smells_data = analyzer_controller.run_analysis(SOURCE)
    output_config.save_json_files(Path("code_smells.json"), smells_data)

    output_config.copy_file_to_output(SOURCE, "refactored-test-case.py")
    refactorer_controller = RefactorerController(OUTPUT_DIR)
    output_paths = []
    for smell in smells_data:
        output_paths.append(refactorer_controller.run_refactorer(SOURCE, smell))

    print(output_paths)


if __name__ == "__main__":
    main()
