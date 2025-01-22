import logging
from pathlib import Path
from typing import Dict, Any
from enum import Enum
import json
import sys
from ecooptimizer.data_wrappers.smell import Smell
from ecooptimizer.utils.ast_parser import parse_file
from ecooptimizer.measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from ecooptimizer.analyzers.pylint_analyzer import PylintAnalyzer
from ecooptimizer.utils.refactorer_factory import RefactorerFactory

outputs_dir = Path("/Users/tanveerbrar/Desktop").resolve()


def custom_serializer(obj: Any):
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    if obj is None:
        return None
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def detect_smells(file_path: Path) -> list[Smell]:
    """
    Detect code smells in a given file.

    Args:
        file_path (Path): Path to the Python file to analyze.

    Returns:
        List[Smell]: A list of detected smells.
    """
    logging.info(f"Starting smell detection for file: {file_path}")
    if not file_path.is_file():
        logging.error(f"File {file_path} does not exist.")
        raise FileNotFoundError(f"File {file_path} does not exist.")

    source_code = parse_file(file_path)
    analyzer = PylintAnalyzer(file_path, source_code)
    analyzer.analyze()
    analyzer.configure_smells()

    smells_data: list[Smell] = analyzer.smells_data
    logging.info(f"Detected {len(smells_data)} code smells.")
    return smells_data


def refactor_smell(file_path: Path, smell: Dict[str, Any]) -> dict[str, Any]:
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
    refactorer = RefactorerFactory.build_refactorer_class(smell["messageId"], outputs_dir)
    if not refactorer:
        logging.error(f"No refactorer implemented for smell {smell['symbol']}.")
        raise NotImplementedError(f"No refactorer implemented for smell {smell['symbol']}.")

    refactorer.refactor(file_path, smell, initial_emissions)

    target_line = smell["line"]
    updated_path = outputs_dir / f"{file_path.stem}_LPLR_line_{target_line}.py"
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
    updated_smells = detect_smells(updated_path)

    # Read refactored code
    with Path.open(updated_path) as file:
        refactored_code = file.read()

    return refactored_code, energy_difference, updated_smells

    return


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Missing required arguments: action and file_path"}))
        return

    action = sys.argv[1]
    file = sys.argv[2]
    file_path = Path(file).resolve()

    try:
        if action == "detect":
            smells = detect_smells(file_path)
            print(json.dumps({"smells": smells}, default=custom_serializer))
        elif action == "refactor":
            smell_input = sys.stdin.read()
            smell_data = json.loads(smell_input)
            smell = smell_data.get("smell")

            if not smell:
                print(json.dumps({"error": "Missing smell object for refactor"}))
                return

            refactored_code, energy_difference, updated_smells = refactor_smell(file_path, smell)
            print(
                json.dumps(
                    {
                        "refactored_code": refactored_code,
                        "energy_difference": energy_difference,
                        "updated_smells": updated_smells,
                    }
                )
            )
        else:
            print(json.dumps({"error": f"Invalid action: {action}"}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
