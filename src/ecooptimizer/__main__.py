import argparse
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory, mkdtemp
import traceback
from typing import Optional
import fnmatch

from ecooptimizer.data_types.custom_fields import AdditionalInfo, Occurence

from .config import EcoConfig
from .data_types.smell import EnergyMeta, Smell
from .utils.output_manager import save_json_files
from .api.routes.refactor_smell import ChangedFile, RefactoredData
from .analyzers.analyzer_controller import AnalyzerController
from .refactorers.refactorer_controller import RefactorerController
from .log_config import CONFIG  # noqa: F401


def parse_smells_arg(smells_str: str) -> dict[str, dict]:  # type: ignore
    """Parse the smells argument into a dictionary format.

    Format: smell1:param1=value1;param2=value2,smell2:param=value

    Example: "cached-repeated-calls:threshold=2;max_depth=3,no-self-use"
    """
    if not smells_str:
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
        else:
            smells[item.strip()] = {}
    return smells


def load_smells_from_file(file_path: Path) -> dict[str, dict]:  # type: ignore
    """Load smells data from a JSON file."""
    try:
        with file_path.open() as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Smells file should contain a dictionary of smell objects")
            if not data:
                raise ValueError("Smells file is empty")
            return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in smells file: {e}") from e
    except Exception as e:
        raise ValueError(f"Error loading smells file: {e}") from e


def should_skip_file(file_path: Path, exclude_patterns: set[str]) -> bool:
    """Check if file should be skipped based on exclude patterns."""
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(str(file_path.resolve()), pattern):
            print(f"Skipped path: {file_path.resolve()}")
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
    analyzer_controller = AnalyzerController()
    smells_data: list[Smell] = []

    def should_process_path(path: Path) -> bool:
        """Check if path should be processed (not excluded)."""
        return not should_skip_file(path, exclude_patterns)

    def scan_directory(directory: Path):
        """Scan a directory with proper exclusion handling."""
        if not should_process_path(directory):
            return

        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix == ".py":
                    if should_process_path(item):
                        smells_data.extend(analyzer_controller.run_analysis(item, smells_config))
                elif recursive and item.is_dir():
                    scan_directory(item)  # Recurse into subdirectory
        except PermissionError:
            print(f"Warning: No permission to access {directory}")

    if target.is_file() and target.suffix == ".py":
        if should_process_path(target):
            smells_data.extend(analyzer_controller.run_analysis(target, smells_config))
    elif target.is_dir():
        print(f"Analyzing directory: {target}")
        print(f"Checking for the following smells: {smells_config}")
        scan_directory(target)
    else:
        print(f"Warning: {target} is not a valid Python file or directory")

    save_json_files(output_file, {smell.id: smell.model_dump() for smell in smells_data})
    print(
        f"Analysis complete. {len(smells_data)} smells found. Results saved to {output_file.name}"
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
    print(f"Refactoring {target} based on code smells...")
    refactorer_controller = RefactorerController()
    output_paths = []
    tempDir = ""

    if save_to_original:
        # If saving to original, we need to ensure the target path is correct
        target_path = target
        root_path = root
    else:
        tempDir = mkdtemp(prefix="ecooptimizer_")
        root_path = Path(tempDir) / root.name
        target_path = Path(str(target).replace(str(root), str(root_path), 1))

        shutil.copytree(root, root_path)

    try:
        modified_files: list[Path] = refactorer_controller.run_refactorer(
            target_path,
            root_path,
            smell,
        )
    except NotImplementedError as e:
        print(f"Refactorer for {smell.get('type')} not found: {e}")

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
    print(f"Refactoring complete. Results saved to {output_file.name}")

    return output_paths


def build_smell(smell_dict: dict) -> Smell:  # type: ignore
    """Build a Smell instance from a dictionary."""
    return Smell(
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


def parse_exclude_patterns(patterns_str: str) -> set[str]:
    """Parse exclude patterns from comma-separated string."""
    if not patterns_str:
        return set()
    return {p.strip() for p in patterns_str.split(",") if p.strip()}


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ecooptimizer",
        description="Code smell analyzer and refactorer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Mode selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-a", "--analyze-only", action="store_true", help="Only analyze for smells, do not refactor"
    )
    group.add_argument(
        "-r",
        "--refactor-only",
        action="store_true",
        help="Only refactor using existing smells data",
    )

    # Target selection
    parser.add_argument(
        "-p",
        "--root",
        type=str,
        default=".",
        help="Root project directory to analyze (default: current directory)",
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=".",
        help="Target file or directory (default: current directory)",
    )
    parser.add_argument(
        "-R",
        "--recursive",
        action="store_true",
        help="Process all Python files in directory recursively",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        type=str,
        default="",
        help='Comma-separated file patterns to exclude (e.g. "test_*,*_mock.py")',
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save analysis results and refactored files",
    )
    parser.add_argument(
        "-na",
        "--analysis-results-file",
        type=str,
        default="code_smells.json",
        help="File to save analysis results (default: code_smells.json)",
    )
    parser.add_argument(
        "-nr",
        "--refactor-results-file",
        type=str,
        default="refactoring-data.json",
        help="File to save refactoring results (default: refactoring-data.json)",
    )

    # Analysis options
    parser.add_argument(
        "-s",
        "--smells",
        type=str,
        default="",
        help="Comma-separated smell specifications with optional params. "
        'Format: "smell1:param1=val1;param2=val2,smell2". '
        'Example: "cached-repeated-calls:threshold=2;max_depth=3,no-self-use"',
    )

    # Refactoring options
    parser.add_argument(
        "-f", "--smells-file", type=str, help="JSON file containing smells data for refactoring"
    )
    parser.add_argument(
        "-i", "--smell-id", type=str, help="Comma-separated list of specific smell IDs to refactor"
    )
    parser.add_argument(
        "-so",
        "--save-to-original",
        action="store_true",
        help="Save refactored files to their original location instead of temp directory",
    )

    return parser


def main(args=None):  # noqa: ANN001
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]

    print("EcoOptimizer CLI - Version 1.0.0")
    # Load config first
    config = EcoConfig.load()

    # Parse CLI args
    parser = create_parser()

    # Combine config and CLI args (CLI args take precedence)
    config_args = config.to_cli_args()
    final_args = config_args + args

    parsed_args = parser.parse_args(final_args)

    target = Path(parsed_args.target).resolve()
    if not target.exists():
        print(f"Error: Target '{target}' does not exist", file=sys.stderr)
        sys.exit(1)

    root = Path(parsed_args.root).resolve()
    if not root.exists():
        print(f"Error: Project root '{root}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Set output directory
    output_dir = Path(parsed_args.output_dir).resolve()
    if not output_dir.exists():
        print(f"Error: Output directory '{output_dir}' does not exist", file=sys.stderr)
        sys.exit(1)
    if not output_dir.is_dir():
        print(f"Error: Output path '{output_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Set analysis results file
    analysis_results_file = output_dir / parsed_args.analysis_results_file
    if analysis_results_file.exists():
        print(
            f"Warning: Analysis results file '{analysis_results_file}' already exists. It will be overwritten."
        )

    # Set refactor results file
    refactor_results_file = output_dir / parsed_args.refactor_results_file
    if refactor_results_file.exists():
        print(
            f"Warning: Refactor results file '{refactor_results_file}' already exists. It will be overwritten."
        )

    exclude_patterns = parse_exclude_patterns(parsed_args.exclude)
    if exclude_patterns:
        print(f"Excluding patterns: {exclude_patterns}")

    # Parse smells configuration
    enabled_smells = parse_smells_arg(parsed_args.smells) if parsed_args.smells else "all"

    if parsed_args.refactor_only:
        if not parsed_args.smells_file or not parsed_args.smell_id:
            print(
                "Error: missing --smells-file or --smell-id which are required for --refactor-only",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            smells_data = load_smells_from_file(Path(parsed_args.smells_file))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        smell = smells_data.get(parsed_args.smell_id)

        if not smell:
            print(
                f"Error: Smell with ID '{parsed_args.smell_id}' not found in {parsed_args.smells_file}",
                file=sys.stderr,
            )
            sys.exit(1)

        output_paths = refactor_code(
            Path(smell["path"]),
            root,
            refactor_results_file,
            build_smell(smell),
            parsed_args.save_to_original,
        )
        print("Refactored files:", output_paths)
    else:
        smells_data = analyze_code(
            target, enabled_smells, exclude_patterns, analysis_results_file, parsed_args.recursive
        )

        if not parsed_args.analyze_only:
            print("Refactoring multiple smells not implemented yet.")
            # output_paths = refactor_code(target, root, refactor_results_file, smells_data)
            # print("Refactored files:", output_paths)


if __name__ == "__main__":
    main()
