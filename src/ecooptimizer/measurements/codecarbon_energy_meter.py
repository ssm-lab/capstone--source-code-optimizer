"""CodeCarbon-based implementation for measuring code energy consumption."""

import logging
import os
from pathlib import Path
import sys
import subprocess
import pandas as pd
from tempfile import TemporaryDirectory
from codecarbon import EmissionsTracker

from ecooptimizer.measurements.base_energy_meter import BaseEnergyMeter


class CodeCarbonEnergyMeter(BaseEnergyMeter):
    """Measures code energy consumption using CodeCarbon's emissions tracker."""

    def __init__(self):
        """Initializes the energy meter with empty emissions data."""
        super().__init__()
        self.emissions_data = None

    def measure_energy(self, file_path: Path) -> None:
        """Executes a file while tracking emissions using CodeCarbon.

        Args:
            file_path: Path to Python file to measure

        Note:
            Creates temporary directory for emissions data
            Handles subprocess execution errors
            Stores emissions data if measurement succeeds
        """
        logging.info(f"Starting CodeCarbon energy measurement on {file_path.name}")

        with TemporaryDirectory() as custom_temp_dir:
            os.environ["TEMP"] = custom_temp_dir  # For Windows
            os.environ["TMPDIR"] = custom_temp_dir  # For Unix-based systems

            # TODO: Save to logger so doesn't print to console
            tracker = EmissionsTracker(
                output_dir=custom_temp_dir,
                allow_multiple_runs=True,
                tracking_mode="process",
                log_level="error",
            )  # type: ignore
            tracker.start()

            try:
                subprocess.run(
                    [sys.executable, file_path], capture_output=True, text=True, check=True
                )
                logging.info("CodeCarbon measurement completed successfully.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error executing file '{file_path}': {e}")
            finally:
                self.emissions = tracker.stop()
                emissions_file = Path(custom_temp_dir) / "emissions.csv"

                if emissions_file.exists():
                    self.emissions_data = self._extract_emissions_data(emissions_file)
                else:
                    logging.error("Emissions file missing - measurement failed")

    def _extract_emissions_data(self, csv_path: Path):
        """Extracts emissions data from CodeCarbon output CSV.

        Args:
            csv_path: Path to emissions CSV file

        Returns:
            dict: Last measurement record from CSV
            None: If extraction fails
        """
        try:
            df = pd.read_csv(csv_path)
            return df.to_dict(orient="records")[-1]
        except Exception as e:
            logging.error(f"Failed to read emissions data: {e}")
            return None
