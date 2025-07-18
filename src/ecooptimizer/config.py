# config.py
from pathlib import Path
from typing import Any, Optional
import tomli  # for Python <3.11
import sys

DEFAULT_CONFIG_PATHS = [
    Path(".ecooptimizer"),
    Path("pyproject.toml"),  # Also check pyproject.toml
]


class EcoConfig:
    def __init__(self):
        self.data: dict[str, Any] = {
            "root": ".",
            "target": ".",
            "output_dir": ".",
            "analysis_results_file": "code_smells.json",
            "refactor_results_file": "refactoring-data.json",
            "recursive": False,
            "save_to_original": False,
            "exclude": [],
            "smells": "all",
            "analyze_only": False,
            "refactor_only": False,
            "smells_file": "code_smells.json",
            "smell_id": None,
        }

    @classmethod
    def find_config_file(cls) -> Optional[Path]:
        """Search for config file in common locations"""
        for path in DEFAULT_CONFIG_PATHS:
            if path.exists():
                print(f"Found config file at: {path}")
                return path

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "EcoConfig":
        """Load config from file"""
        instance = cls()

        if config_path is None:
            config_path = cls.find_config_file()

        if config_path:
            try:
                with config_path.open(mode="rb") as f:
                    if config_path.name == "pyproject.toml":
                        data = tomli.load(f)
                        eco_config = data.get("tool", {}).get("ecooptimizer", {})
                    else:
                        eco_config = tomli.load(f)

                    instance.data.update(eco_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}", file=sys.stderr)

        return instance

    def to_cli_args(self) -> list[str]:
        """Convert config to equivalent CLI args"""
        args = []

        if self.data.get("analyze_only"):
            args.append("--analyze-only")
        if self.data.get("refactor_only"):
            args.append("--refactor-only")
        if self.data.get("recursive"):
            args.append("--recursive")
        if self.data.get("save_to_original"):
            args.append("--save-to-original")

        if self.data.get("output_dir") != ".":
            args.extend(["--output-dir", str(self.data["output_dir"])])

        if self.data.get("analysis_results_file") != "code_smells.json":
            args.extend(["--analysis-results-file", str(self.data["analysis_results_file"])])

        if self.data.get("refactor_results_file") != "refactoring-data.json":
            args.extend(["--refactor-results-file", str(self.data["refactor_results_file"])])

        if self.data.get("root") != ".":
            args.extend(["--root", str(self.data["root"])])

        if self.data.get("target") != ".":
            args.extend(["--target", str(self.data["target"])])

        if self.data.get("exclude"):
            args.extend(["--exclude", ",".join(self.data["exclude"])])

        if self.data.get("smell_id"):
            args.extend(["--smell-id", str(self.data["smell_id"])])

        if self.data.get("smells_file") != "code_smells.json":
            args.extend(["--smells-file", str(self.data["smells_file"])])

        if self.data.get("smells") != "all":
            smell_specs = []
            for name, params in self.data["smells"]:
                if params:
                    params_str = ";".join(f"{k}={v}" for k, v in params.items())
                    smell_specs.append(f"{name}:{params_str}")
                else:
                    smell_specs.append(name)
            args.extend(["--smells", ",".join(smell_specs)])

        return args
