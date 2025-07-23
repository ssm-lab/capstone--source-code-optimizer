import argparse
import json
from pathlib import Path
import shutil
import sys
from tempfile import mkdtemp
import traceback
import fnmatch
import logging

from ecooptimizer.data_types.custom_fields import AdditionalInfo, Occurence

from .config import EcoConfig
from .data_types.smell import EnergyMeta, Smell
from .utils.output_manager import LoggingManager, save_json_files
from .api.routes.refactor_smell import ChangedFile, RefactoredData
from .analyzers.analyzer_controller import AnalyzerController
from .refactorers.refactorer_controller import RefactorerController
from .log_config import CONFIG  # noqa: F401


# Placeholder for logger initialization
logger = logging.getLogger()
rlogger = logging.getLogger("refactor")
alogger = logging.getLogger("detect")


def parse_smells_arg(smells_str: str) -> dict[str, dict]:  # type: ignore
    """Parse the smells argument into a dictionary format.

    Format: smell1:param1=value1;param2=value2,smell2:param=value

    Example: "cached-repeated-calls:threshold=2;max_depth=3,no-self-use"
    """
    logging.debug(f"Starting to parse smells argument: {smells_str}")
    if not smells_str:
        logging.debug("Empty smells string provided, returning empty dict")
        return {}

    smells = {}
    for item in smells_str.split(","):
        item = item.strip()
        if not item:
            continue

        if ":" in item:
            name, params = item.split(":", 1)
            params_dict = {}
            for param in params.split(";"):
                param = param.strip()
                if not param:
                    continue
                if "=" in param:
                    k, v = param.split("=", 1)
                    try:
                        # Try to convert to int if possible
                        v = int(v)
                    except ValueError:
                        try:
                            # Try to convert to float if possible
                            v = float(v)
                        except ValueError:
                            pass
                    params_dict[k.strip()] = v
            smells[name.strip()] = params_dict
            logging.debug(f"Parsed smell '{name}' with params: {params_dict}")
        else:
            smells[item.strip()] = {}
            logging.debug(f"Parsed smell '{item}' with no params")

    logging.info(f"Successfully parsed {len(smells)} smell configurations")
    return smells


def load_smells_from_file(file_path: Path) -> dict[str, dict]:  # type: ignore
    """Load smells data from a JSON file."""
    logging.info(f"Attempting to load smells from file: {file_path}")
    try:
        with file_path.open() as f:
            data = json.load(f)
            if not isinstance(data, dict):
                error_msg = "Smells file should contain a dictionary of smell objects"
                logging.error(error_msg)
                raise ValueError(error_msg)
            if not data:
                error_msg = "Smells file is empty"
                logging.warning(error_msg)
                raise ValueError(error_msg)
            logging.info(f"Successfully loaded {len(data)} smells from file")
            return data
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format in smells file: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"Error loading smells file: {e}"
        logging.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e


def should_skip_file(file_path: Path, exclude_patterns: set[str]) -> bool:
    """Check if file should be skipped based on exclude patterns."""
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(str(file_path.resolve()), pattern):
            logging.debug(f"Skipping file {file_path} as it matches exclude pattern: {pattern}")
            return True
    return False


def analyze_code(
    target: Path,
    smells_config: dict | str,  # type: ignore
    exclude_patterns: set[str],
    output_file: Path,
    recursive: bool = False,
) -> list[Smell]:
    """Analyze code for smells with proper recursive exclusion checking."""
    alogger.info(f"Starting code analysis on target: {target}")
    alogger.debug(f"Smells config: {smells_config}")
    alogger.debug(f"Exclude patterns: {exclude_patterns}")
    alogger.debug(f"Recursive mode: {recursive}")

    analyzer_controller = AnalyzerController()
    smells_data: list[Smell] = []

    def should_process_path(path: Path) -> bool:
        """Check if path should be processed (not excluded)."""
        return not should_skip_file(path, exclude_patterns)

    def scan_directory(directory: Path):
        """Scan a directory with proper exclusion handling."""
        if not should_process_path(directory):
            alogger.debug(f"Skipping excluded directory: {directory}")
            return

        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix == ".py":
                    if should_process_path(item):
                        alogger.debug(f"Analyzing file: {item}")
                        smells_data.extend(analyzer_controller.run_analysis(item, smells_config))
                elif recursive and item.is_dir():
                    alogger.debug(f"Entering subdirectory: {item}")
                    scan_directory(item)  # Recurse into subdirectory
        except PermissionError as e:
            alogger.warning(f"No permission to access {directory}: {e}")

    if target.is_file() and target.suffix == ".py":
        if should_process_path(target):
            alogger.info(f"Analyzing single file: {target}")
            smells_data.extend(analyzer_controller.run_analysis(target, smells_config))
        else:
            alogger.info(f"Skipping excluded file: {target}")
    elif target.is_dir():
        alogger.info(f"Analyzing directory: {target}")
        alogger.info(f"Checking for the following smells: {smells_config}")
        scan_directory(target)
    else:
        alogger.warning(f"{target} is not a valid Python file or directory")

    save_json_files(output_file, {smell.id: smell.model_dump() for smell in smells_data})
    alogger.info(
        f"Analysis complete. Found {len(smells_data)} smells. Results saved to {output_file}"
    )
    return smells_data


def refactor_code(
    target: Path,
    root: Path,
    output_file: Path,
    smell: Smell,
    save_to_original: bool = False,
) -> list[ChangedFile]:
    """Refactor code based on smells data."""
    rlogger.info(f"Starting refactoring for target: {target}")
    rlogger.debug(f"Smell being refactored: {smell.type} (ID: {smell.id})")
    rlogger.debug(f"Root directory: {root}")
    rlogger.debug(f"Save to original: {save_to_original}")

    refactorer_controller = RefactorerController()
    output_paths = []
    tempDir = ""

    if save_to_original:
        rlogger.warning("Refactoring will modify original files directly")
        target_path = target
        root_path = root
    else:
        tempDir = mkdtemp(prefix="ecooptimizer_")
        rlogger.debug(f"Created temporary directory: {tempDir}")
        root_path = Path(tempDir) / root.name
        target_path = Path(str(target).replace(str(root), str(root_path), 1))

        rlogger.debug(f"Copying project to temporary '{tempDir}' directory for safe refactoring")
        shutil.copytree(root, root_path)

    try:
        rlogger.info(f"Running refactorer for smell type: {smell.type}")
        modified_files: list[Path] = refactorer_controller.run_refactorer(
            target_path,
            root_path,
            smell,
        )
        rlogger.debug(f"Refactoring completed. Modified {len(modified_files)} files")
    except NotImplementedError as e:
        error_msg = f"Refactorer for {smell.type} not implemented: {e}"
        rlogger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Error during refactoring: {e}"
        rlogger.error(error_msg, exc_info=True)
        raise

    refactor_data = RefactoredData(
        tempDir=tempDir,
        targetFile=ChangedFile(original=str(target), refactored=str(target_path)),
        energySaved=0,
        affectedFiles=[
            ChangedFile(
                original=str(file).replace(str(root_path), str(root)),
                refactored=str(file),
            )
            for file in modified_files  # type: ignore
        ],
    )

    output_paths.extend(refactor_data.affectedFiles)
    save_json_files(output_file, refactor_data.model_dump())
    rlogger.info(f"Refactoring complete. Results saved to {output_file}")
    rlogger.debug(f"Affected files: {output_paths}")

    return output_paths


def build_smell(smell_dict: dict) -> Smell:  # type: ignore
    """Build a Smell instance from a dictionary."""
    logging.debug(f"Building Smell object from dict: {smell_dict}")
    try:
        smell = Smell(
            id=smell_dict.get("id"),
            confidence=smell_dict["confidence"],
            message=smell_dict["message"],
            messageId=smell_dict["messageId"],
            module=smell_dict["module"],
            obj=smell_dict.get("obj"),
            path=smell_dict["path"],
            symbol=smell_dict["symbol"],
            type=smell_dict["type"],
            occurences=[Occurence(**occ) for occ in smell_dict.get("occurences", [])],
            additionalInfo=AdditionalInfo(**smell_dict["additionalInfo"])
            if "additionalInfo" in smell_dict
            else None,
            energyMetadata=EnergyMeta(**smell_dict["energyMetadata"])
            if "energyMetadata" in smell_dict
            else None,
        )
        logging.debug(f"Successfully built Smell object with ID: {smell.id}")
        return smell
    except Exception as e:
        logging.error(f"Error building Smell object: {e}", exc_info=True)
        raise


def parse_exclude_patterns(patterns_str: str) -> set[str]:
    """Parse exclude patterns from comma-separated string."""
    logging.debug(f"Parsing exclude patterns from: {patterns_str}")
    if not patterns_str:
        logging.debug("No exclude patterns provided")
        return set()
    patterns = {p.strip() for p in patterns_str.split(",") if p.strip()}
    logging.debug(f"Parsed {len(patterns)} exclude patterns")
    return patterns


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    logging.debug("Creating argument parser")
    parser = argparse.ArgumentParser(
        prog="ecooptimizer",
        description="Code smell analyzer and refactorer",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        description="valid commands",
        help='Perform actions like "analyze" or "refactor"',
    )

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze code for smells",
    )

    analyze_parser.add_argument(
        "-l",
        "--log-dir",
        type=str,
        help="Directory where the log files will be outputted to.",
    )

    # Target selection for analyze
    analyze_parser.add_argument(
        "-p",
        "--root",
        type=str,
        default=".",
        help="Root project directory to analyze (default: current directory)",
    )
    analyze_parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=".",
        help="Target file or directory (default: current directory)",
    )
    analyze_parser.add_argument(
        "-R",
        "--recursive",
        action="store_true",
        help="Process all Python files in directory recursively",
    )
    analyze_parser.add_argument(
        "-x",
        "--exclude",
        type=str,
        default="",
        help='Comma-separated file patterns to exclude (e.g. "test_*,*_mock.py")',
    )
    analyze_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save analysis results",
    )
    analyze_parser.add_argument(
        "-na",
        "--analysis-results-file",
        type=str,
        default="code_smells.json",
        help="File to save analysis results (default: code_smells.json)",
    )

    # Analysis options
    analyze_parser.add_argument(
        "-s",
        "--smells",
        type=str,
        default="",
        help="Comma-separated smell specifications with optional params. "
        'Format: "smell1:param1=val1;param2=val2,smell2". '
        'Example: "cached-repeated-calls:threshold=2;max_depth=3,no-self-use"',
    )

    # Refactor command
    refactor_parser = subparsers.add_parser(
        "refactor",
        help="Refactor code using existing smells data",
    )

    refactor_parser.add_argument(
        "smells_file", type=str, help="JSON file containing smells data for refactoring"
    )

    refactor_parser.add_argument(
        "-l",
        "--log-dir",
        type=str,
        help="Directory where the log files will be outputted to.",
    )

    # Target selection for refactor
    refactor_parser.add_argument(
        "-p",
        "--root",
        type=str,
        default=".",
        help="Root project directory (default: current directory)",
    )
    refactor_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save refactored files",
    )
    refactor_parser.add_argument(
        "-nr",
        "--refactor-results-file",
        type=str,
        default="refactoring-data.json",
        help="File to save refactoring results (default: refactoring-data.json)",
    )
    refactor_parser.add_argument(
        "-i",
        "--smell-id",
        type=str,
        help="Specific smell ID to refactor",
    )
    refactor_parser.add_argument(
        "-so",
        "--save-to-original",
        action="store_true",
        help="Save refactored files to their original location instead of temp directory",
    )

    logging.debug("Argument parser configuration complete")
    return parser


def main(args=None):
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]

    print("EcoOptimizer CLI - Version 1.0.0")

    # Create parser and parse just the command first
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument("command", choices=["analyze", "refactor"], help="Subcommand to run")
    cmd_args, remaining_args = base_parser.parse_known_args(args)

    # Load config after we know the command
    try:
        config = EcoConfig.load()
    except Exception:
        traceback.print_exc()
        sys.exit(1)

    # Get command-specific defaults from config
    config_args = config.to_cli_args(cmd_args.command)

    # Now parse full arguments with CLI taking precedence
    parser = create_parser()
    final_args = remaining_args + config_args  # CLI args override config args

    try:
        parsed_args = parser.parse_args([cmd_args.command, *final_args])
    except Exception:
        traceback.print_exc()
        sys.exit(1)

    if parsed_args.log_dir:
        log_manager = LoggingManager(Path(parsed_args.log_dir), production=True)
    else:
        log_manager = LoggingManager(Path("logs").resolve(), production=True)

    root = Path(parsed_args.root).resolve()
    if not root.exists():
        logging.error(f"Project root '{root}' does not exist")
        sys.exit(1)

    # Set output directory
    output_dir = Path(parsed_args.output_dir).resolve()
    if not output_dir.exists():
        logging.error(f"Output directory '{output_dir}' does not exist")
        sys.exit(1)
    if not output_dir.is_dir():
        logging.error(f"Output path '{output_dir}' is not a directory")
        sys.exit(1)

    if parsed_args.command == "analyze":
        # Set analysis results file
        analysis_results_file = output_dir / parsed_args.analysis_results_file
        if analysis_results_file.exists():
            logging.warning(
                f"Analysis results file '{analysis_results_file}' exists and will be overwritten"
            )

        target = Path(parsed_args.target).resolve()
        if not target.exists():
            logging.error(f"Target '{target}' does not exist")
            sys.exit(1)

        exclude_patterns = parse_exclude_patterns(parsed_args.exclude)
        if exclude_patterns:
            logging.info(f"Excluding patterns: {exclude_patterns}")

        # Parse smells configuration
        enabled_smells = parse_smells_arg(parsed_args.smells) if parsed_args.smells else "all"
        logging.info(f"Enabled smells configuration: {enabled_smells}")

        try:
            smells_data = analyze_code(
                target,
                enabled_smells,
                exclude_patterns,
                analysis_results_file,
                parsed_args.recursive,
            )
            logging.info("Analysis phase completed successfully")
        except Exception as e:
            logging.error(f"Analysis failed: {e}", exc_info=True)
            sys.exit(1)

    elif parsed_args.command == "refactor":
        # Set refactor results file
        refactor_results_file = output_dir / parsed_args.refactor_results_file
        if refactor_results_file.exists():
            logging.warning(
                f"Refactor results file '{refactor_results_file}' exists and will be overwritten"
            )

        try:
            smells_data = load_smells_from_file(Path(parsed_args.smells_file))
        except ValueError as e:
            logging.error(f"Failed to load smells file: {e}")
            sys.exit(1)

        if parsed_args.smell_id:
            # Refactor specific smell
            smell = smells_data.get(parsed_args.smell_id)
            if not smell:
                logging.error(
                    f"Smell with ID '{parsed_args.smell_id}' not found in {parsed_args.smells_file}"
                )
                sys.exit(1)

            print(f"Refactoring smell: {smell['message']} (ID: {smell['id']})")

            try:
                output_paths = refactor_code(
                    Path(smell["path"]),
                    root,
                    refactor_results_file,
                    build_smell(smell),
                    parsed_args.save_to_original,
                )
                logging.info(f"Refactoring completed successfully. Modified files: {output_paths}")
                print("Refactoring completed successfully.")
            except Exception as e:
                print(f"Refactoring failed: {e}")
                logging.error(f"Refactoring failed: {e}", exc_info=True)
                sys.exit(1)
        else:
            # Placeholder for future batch refactoring implementation
            logging.error(
                "Batch refactoring of all smells is not yet implemented due to line number synchronization issues"
            )
            sys.exit(1)

    logging.info("EcoOptimizer CLI completed successfully")


if __name__ == "__main__":
    main()
