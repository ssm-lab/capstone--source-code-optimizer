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
            "analyze": {
                "root": ".",
                "target": ".",
                "output_dir": ".",
                "log_dir": "",
                "analysis_results_file": "code_smells.json",
                "recursive": False,
                "exclude": [],
                "smells": "all",
            },
            "refactor": {
                "root": ".",
                "output_dir": ".",
                "log_dir": "",
                "refactor_results_file": "refactoring-data.json",
                "save_to_original": False,
                "smells_file": "code_smells.json",
                "smell_id": None,
            },
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

                    # Handle both old and new config formats
                    if "command" in eco_config:
                        # New format with subcommands
                        instance.data.update(eco_config)
                    else:
                        # Old format - convert to new structure
                        instance._convert_old_config(eco_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}", file=sys.stderr)

        return instance

    def _convert_old_config(self, config_data: dict[str, Any]) -> None:
        """Convert old config format to new subcommand-based format"""
        # Determine command based on old flags
        if config_data.get("analyze_only"):
            self.data["command"] = "analyze"
        elif config_data.get("refactor_only"):
            self.data["command"] = "refactor"

        # Move analyze-related options
        analyze_keys = [
            "root",
            "target",
            "output_dir",
            "log_dir",
            "analysis_results_file",
            "recursive",
            "exclude",
            "smells",
        ]
        for key in analyze_keys:
            if key in config_data:
                self.data["analyze"][key] = config_data[key]

        # Move refactor-related options
        refactor_keys = [
            "root",
            "output_dir",
            "log_dir",
            "refactor_results_file",
            "save_to_original",
            "smells_file",
            "smell_id",
        ]
        for key in refactor_keys:
            if key in config_data:
                self.data["refactor"][key] = config_data[key]

    def to_cli_args(self, command: str) -> list[str]:
        """Convert config to CLI args for specific command"""
        args = []
        cmd_config = self.data.get(command, {})

        if command == "analyze":
            if cmd_config.get("root") != ".":
                args.extend(["--root", str(cmd_config["root"])])
            if cmd_config.get("target") != ".":
                args.extend(["--target", str(cmd_config["target"])])
            if cmd_config.get("output_dir") != ".":
                args.extend(["--output-dir", str(cmd_config["output_dir"])])
            if cmd_config.get("log_dir"):
                args.extend(["--log-dir", str(cmd_config["log_dir"])])
            if cmd_config.get("analysis_results_file") != "code_smells.json":
                args.extend(["--analysis-results-file", str(cmd_config["analysis_results_file"])])
            if cmd_config.get("recursive"):
                args.append("--recursive")
            if cmd_config.get("exclude"):
                args.extend(["--exclude", ",".join(cmd_config["exclude"])])
            if cmd_config.get("smells") != "all":
                if isinstance(cmd_config["smells"], dict):
                    smell_specs = []
                    for name, params in cmd_config["smells"].items():
                        if params:
                            params_str = ";".join(f"{k}={v}" for k, v in params.items())
                            smell_specs.append(f"{name}:{params_str}")
                        else:
                            smell_specs.append(name)
                    args.extend(["--smells", ",".join(smell_specs)])
                else:
                    args.extend(["--smells", str(cmd_config["smells"])])

        elif command == "refactor":
            if cmd_config.get("smells_file") != "code_smells.json":
                args.append(str(cmd_config["smells_file"]))
            if cmd_config.get("root") != ".":
                args.extend(["--root", str(cmd_config["root"])])
            if cmd_config.get("output_dir") != ".":
                args.extend(["--output-dir", str(cmd_config["output_dir"])])
            if cmd_config.get("log_dir"):
                args.extend(["--log-dir", str(cmd_config["log_dir"])])
            if cmd_config.get("refactor_results_file") != "refactoring-data.json":
                args.extend(["--refactor-results-file", str(cmd_config["refactor_results_file"])])
            if cmd_config.get("save_to_original"):
                args.append("--save-to-original")
            if cmd_config.get("smell_id"):
                args.extend(["--smell-id", str(cmd_config["smell_id"])])

        return args
