from pathlib import Path

from ecooptimizer.analyzers.analyzer_controller import AnalyzerController

from .utils.outputs_config import OutputConfig

from .refactorers.refactorer_controller import RefactorerController

# Path of current directory
DIRNAME = Path(__file__).parent
# Path to output folder
OUTPUT_DIR = (DIRNAME / Path("../../outputs")).resolve()
# Path to log file
LOG_FILE = OUTPUT_DIR / Path("log.log")
# Path to the file to be analyzed
TEST_FILE = (DIRNAME / Path("../../tests/input/inefficient_code_example_1.py")).resolve()


def main():
    output_config = OutputConfig(OUTPUT_DIR)

    analyzer_controller = AnalyzerController()
    smells_data = analyzer_controller.run_analysis(TEST_FILE)
    output_config.save_json_files(Path("code_smells.json"), smells_data)

    output_config.copy_file_to_output(TEST_FILE, "refactored-test-case.py")
    refactorer_controller = RefactorerController(OUTPUT_DIR)
    output_paths = []
    for smell in smells_data:
        output_paths.append(refactorer_controller.run_refactorer(TEST_FILE, smell))

    print(output_paths)


if __name__ == "__main__":
    main()
