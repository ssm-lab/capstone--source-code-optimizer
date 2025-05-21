import argparse
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from typing import List, Dict, Optional, Set
import fnmatch

from .data_types.smell import Smell
from .utils.output_manager import save_json_files
from .api.routes.refactor_smell import ChangedFile, RefactoredData
from .analyzers.analyzer_controller import AnalyzerController
from .refactorers.refactorer_controller import RefactorerController
from . import SAMPLE_PROJ_DIR, SOURCE
from .log_config import CONFIG

def parse_smells_arg(smells_str: str) -> Dict[str, Dict]:
    """Parse the smells argument into a dictionary format.
    
    Format: smell1:param1=value1;param2=value2,smell2:param=value
    
    Example: "cached-repeated-calls:threshold=2;max_depth=3,no-self-use"
    """
    if not smells_str:
        return {}
    
    smells = {}
    for item in smells_str.split(','):
        item = item.strip()
        if not item:
            continue
            
        if ':' in item:
            name, params = item.split(':', 1)
            params_dict = {}
            for param in params.split(';'):
                param = param.strip()
                if not param:
                    continue
                if '=' in param:
                    k, v = param.split('=', 1)
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

def load_smells_from_file(file_path: Path) -> List[Smell]:
    """Load smells data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Smells file should contain a list of smell objects")
            if not data:
                raise ValueError("Smells file is empty")
            return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in smells file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading smells file: {e}")

def should_skip_file(file_path: Path, exclude_patterns: Set[str]) -> bool:
    """Check if file should be skipped based on exclude patterns."""
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(file_path.name, pattern):
            return True
    return False

def analyze_code(target: Path, smells_config: Dict | str, exclude_patterns: Set[str], recursive: bool = False) -> List[Smell]:
    """Analyze code for smells."""
    analyzer_controller = AnalyzerController()
    smells_data = []
    
    if target.is_dir():
        if recursive:
            for py_file in target.rglob('*.py'):
                if should_skip_file(py_file, exclude_patterns):
                    continue
                smells_data.extend(analyzer_controller.run_analysis(py_file, smells_config))
        else:
            for py_file in target.glob('*.py'):
                if should_skip_file(py_file, exclude_patterns):
                    continue
                smells_data.extend(analyzer_controller.run_analysis(py_file, smells_config))
    else:
        smells_data = analyzer_controller.run_analysis(target, smells_config)
    
    save_json_files("code_smells.json", [smell.model_dump() for smell in smells_data])
    return smells_data

def refactor_code(target: Path, smells_data: List[Smell], smell_ids: Optional[List[str]] = None, 
                 smell_types: Optional[List[str]] = None, exclude_patterns: Set[str] = None) -> List[ChangedFile]:
    """Refactor code based on smells data."""
    if exclude_patterns is None:
        exclude_patterns = set()
        
    refactorer_controller = RefactorerController()
    output_paths = []
    
    # Filter smells if specific IDs or types are provided
    filtered_smells = smells_data
    if smell_ids:
        filtered_smells = [smell for smell in filtered_smells if smell.get('id') in smell_ids]
    if smell_types:
        filtered_smells = [smell for smell in filtered_smells if smell.get('type') in smell_types]
    
    for smell in filtered_smells:
        with TemporaryDirectory() as tempDir:
            source_copy = Path(tempDir) / SAMPLE_PROJ_DIR.name
            target_file_copy = Path(str(target).replace(str(SAMPLE_PROJ_DIR), str(source_copy), 1))
            
            shutil.copytree(SAMPLE_PROJ_DIR, source_copy)
            
            try:
                modified_files: List[Path] = refactorer_controller.run_refactorer(
                    target_file_copy, source_copy, smell, overwrite=False
                )
            except NotImplementedError as e:
                print(f"Skipping refactoring for {smell.get('type')}: {e}")
                continue
            
            refactor_data = RefactoredData(
                tempDir=tempDir,
                targetFile=ChangedFile(original=str(target), refactored=str(target_file_copy)),
                affectedFiles=[
                    ChangedFile(
                        original=str(file).replace(str(source_copy), str(SAMPLE_PROJ_DIR)),
                        refactored=str(file),
                    )
                    for file in modified_files
                    if not should_skip_file(file, exclude_patterns)
                ],
            )
            
            output_paths.extend(refactor_data.affectedFiles)
            save_json_files("refactoring-data.json", refactor_data.model_dump())
    
    return output_paths

def parse_exclude_patterns(patterns_str: str) -> Set[str]:
    """Parse exclude patterns from comma-separated string."""
    if not patterns_str:
        return set()
    return {p.strip() for p in patterns_str.split(',') if p.strip()}

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog='ecooptimizer',
        description='Code smell analyzer and refactorer',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Mode selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--analyze-only', action='store_true', 
                      help='Only analyze for smells, do not refactor')
    group.add_argument('-r', '--refactor-only', action='store_true', 
                      help='Only refactor using existing smells data')
    
    # Target selection
    parser.add_argument('-t', '--target', type=str, default='.', 
                       help='Target file or directory (default: current directory)')
    parser.add_argument('-R', '--recursive', action='store_true', 
                       help='Process all Python files in directory recursively')
    parser.add_argument('-x', '--exclude', type=str, default='', 
                       help='Comma-separated file patterns to exclude (e.g. "test_*,*_mock.py")')
    
    # Analysis options
    parser.add_argument('-s', '--smells', type=str, default='', 
                       help='Comma-separated smell specifications with optional params. '
                            'Format: "smell1:param1=val1;param2=val2,smell2". '
                            'Example: "cached-repeated-calls:threshold=2;max_depth=3,no-self-use"')
    
    # Refactoring options
    parser.add_argument('-f', '--smells-file', type=str, 
                       help='JSON file containing smells data for refactoring')
    parser.add_argument('-i', '--smell-ids', type=str, 
                       help='Comma-separated list of specific smell IDs to refactor')
    parser.add_argument('-y', '--smell-types', type=str, 
                       help='Comma-separated list of specific smell types to refactor')
    
    return parser

def main(args=None):
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]
    
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    target = Path(parsed_args.target).resolve()
    if not target.exists():
        print(f"Error: Target '{target}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    exclude_patterns = parse_exclude_patterns(parsed_args.exclude)
    
    # Parse smells configuration
    enabled_smells = parse_smells_arg(parsed_args.smells) if parsed_args.smells else "all"
    
    if parsed_args.refactor_only:
        if not parsed_args.smells_file:
            print("Error: --smells-file is required for --refactor-only", file=sys.stderr)
            sys.exit(1)
        
        try:
            smells_data = load_smells_from_file(Path(parsed_args.smells_file))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        
        smell_ids = parsed_args.smell_ids.split(',') if parsed_args.smell_ids else None
        smell_types = parsed_args.smell_types.split(',') if parsed_args.smell_types else None
        
        output_paths = refactor_code(
            target, smells_data, smell_ids, smell_types, exclude_patterns
        )
        print("Refactored files:", output_paths)
    else:
        smells_data = analyze_code(target, enabled_smells, exclude_patterns, parsed_args.recursive)
        
        if not parsed_args.analyze_only:
            output_paths = refactor_code(target, smells_data, exclude_patterns=exclude_patterns)
            print("Refactored files:", output_paths)

if __name__ == "__main__":
    main()