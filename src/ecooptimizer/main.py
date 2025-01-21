import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
import argparse
import json
from ecooptimizer.utils.ast_parser import parse_file
from ecooptimizer.utils.outputs_config import OutputConfig
from ecooptimizer.measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
from ecooptimizer.utils.refactorer_factory import RefactorerFactory


class SCOptimizer:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.logs_dir = base_dir / "logs"
        self.outputs_dir = base_dir / "outputs"

        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        self.setup_logging()
        self.output_config = OutputConfig(self.outputs_dir)

    def setup_logging(self):
        """
        Configures logging to write logs to the logs directory.
        """
        log_file = self.logs_dir / "scoptimizer.log"
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            datefmt="%H:%M:%S",
            format="%(asctime)s [%(levelname)s] %(message)s",
        )
        print("****")
        print(log_file)
        logging.info("Logging initialized for Source Code Optimizer. Writing logs to: %s", log_file)

    def detect_smells(self, file_path: Path) -> Dict[str, Any]:
        """Detect code smells in a given file."""
        logging.info(f"Starting smell detection for file: {file_path}")
        if not file_path.is_file():
            logging.error(f"File {file_path} does not exist.")
            raise FileNotFoundError(f"File {file_path} does not exist.")

        logging.info("LOGGGGINGG")

        source_code = parse_file(file_path)
        analyzer = PylintAnalyzer(file_path, source_code)
        analyzer.analyze()
        analyzer.configure_smells()

        smells_data = analyzer.smells_data
        logging.info(f"Detected {len(smells_data)} code smells.")
        return smells_data

    def refactor_smell(self, file_path: Path, smell: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(
            f"Starting refactoring for file: {file_path} and smell symbol: {smell['symbol']} at line {smell['line']}"
        )

        if not file_path.is_file():
            logging.error(f"File {file_path} does not exist.")
            raise FileNotFoundError(f"File {file_path} does not exist.")

        # Measure initial energy
        energy_meter = CodeCarbonEnergyMeter(file_path)
        energy_meter.measure_energy()
        initial_emissions = energy_meter.emissions

        if not initial_emissions:
            logging.error("Could not retrieve initial emissions.")
            raise RuntimeError("Could not retrieve initial emissions.")

        logging.info(f"Initial emissions: {initial_emissions}")

        # Refactor the code smell
        refactorer = RefactorerFactory.build_refactorer_class(smell["messageId"], self.outputs_dir)
        if not refactorer:
            logging.error(f"No refactorer implemented for smell {smell['symbol']}.")
            raise NotImplementedError(f"No refactorer implemented for smell {smell['symbol']}.")

        refactorer.refactor(file_path, smell, initial_emissions)

        target_line = smell["line"]
        updated_path = self.outputs_dir / f"{file_path.stem}_LPLR_line_{target_line}.py"
        logging.info(f"Refactoring completed. Updated file: {updated_path}")

        # Measure final energy
        energy_meter.measure_energy()
        final_emissions = energy_meter.emissions

        if not final_emissions:
            logging.error("Could not retrieve final emissions.")
            raise RuntimeError("Could not retrieve final emissions.")

        logging.info(f"Final emissions: {final_emissions}")

        energy_difference = initial_emissions - final_emissions
        logging.info(f"Energy difference: {energy_difference}")

        # Detect remaining smells
        updated_smells = self.detect_smells(updated_path)

        # Read refactored code
        with open(updated_path) as file:
            refactored_code = file.read()

        result = {
            "refactored_code": refactored_code,
            "energy_difference": energy_difference,
            "updated_smells": updated_smells,
        }

        return result


if __name__ == "__main__":
    default_temp_dir = Path(tempfile.gettempdir()) / "scoptimizer"
    LOG_DIR = os.getenv("LOG_DIR", str(default_temp_dir))
    base_dir = Path(LOG_DIR)
    optimizer = SCOptimizer(base_dir)

    parser = argparse.ArgumentParser(description="Source Code Optimizer CLI Tool")
    parser.add_argument(
        "action",
        choices=["detect", "refactor"],
        help="Action to perform: detect smells or refactor a smell.",
    )
    parser.add_argument("file", type=str, help="Path to the Python file to process.")
    parser.add_argument(
        "--smell",
        type=str,
        required=False,
        help="JSON string of the smell to refactor (required for 'refactor' action).",
    )

    args = parser.parse_args()
    file_path = Path(args.file).resolve()

    if args.action == "detect":
        smells = optimizer.detect_smells(file_path)
        print(smells)
        print("***")
        print(json.dumps(smells))

    elif args.action == "refactor":
        if not args.smell:
            logging.error("--smell argument is required for 'refactor' action.")
            raise ValueError("--smell argument is required for 'refactor' action.")
        smell = json.loads(args.smell)
        result = optimizer.refactor_smell(file_path, smell)
        print(json.dumps(result))
