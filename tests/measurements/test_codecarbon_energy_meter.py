import pytest
import logging
from pathlib import Path
import subprocess
import pandas as pd
from unittest.mock import patch
import sys

from ecooptimizer.measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter


@pytest.fixture
def energy_meter():
    return CodeCarbonEnergyMeter()


@patch("codecarbon.EmissionsTracker.start")
@patch("codecarbon.EmissionsTracker.stop", return_value=0.45)
@patch("subprocess.run")
def test_measure_energy_success(mock_run, mock_stop, mock_start, energy_meter, caplog):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["python3", "../input/project_car_stuff/main.py"], returncode=0
    )
    file_path = Path("../input/project_car_stuff/main.py")
    with caplog.at_level(logging.INFO):
        energy_meter.measure_energy(file_path)

    assert mock_run.call_count >= 1
    mock_run.assert_any_call(
        [sys.executable, file_path],
        capture_output=True,
        text=True,
        check=True,
    )
    mock_start.assert_called_once()
    mock_stop.assert_called_once()
    assert "CodeCarbon measurement completed successfully." in caplog.text
    assert energy_meter.emissions == 0.45


@patch("codecarbon.EmissionsTracker.start")
@patch("codecarbon.EmissionsTracker.stop", return_value=0.45)
@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "python3"))
def test_measure_energy_failure(mock_run, mock_stop, mock_start, energy_meter, caplog):
    file_path = Path("../input/project_car_stuff/main.py")
    with caplog.at_level(logging.ERROR):
        energy_meter.measure_energy(file_path)

    mock_start.assert_called_once()
    mock_run.assert_called_once()
    mock_stop.assert_called_once()
    assert "Error executing file" in caplog.text
    assert (
        energy_meter.emissions_data is None
    )  # since execution failed, emissions data should be None


@patch("pandas.read_csv")
@patch("pathlib.Path.exists", return_value=True)  # mock file existence
def test_extract_emissions_csv_success(mock_exists, mock_read_csv, energy_meter):  # noqa: ARG001
    # simulate DataFrame return value
    mock_read_csv.return_value = pd.DataFrame(
        [{"timestamp": "2025-03-01 12:00:00", "emissions": 0.45}]
    )

    csv_path = Path("dummy_path.csv")  # fake path
    result = energy_meter.extract_emissions_csv(csv_path)

    assert isinstance(result, dict)
    assert "emissions" in result
    assert result["emissions"] == 0.45


@patch("pandas.read_csv", side_effect=Exception("File read error"))
@patch("pathlib.Path.exists", return_value=True)  # mock file existence
def test_extract_emissions_csv_failure(mock_exists, mock_read_csv, energy_meter, caplog):  # noqa: ARG001
    csv_path = Path("dummy_path.csv")  # fake path
    with caplog.at_level(logging.INFO):
        result = energy_meter.extract_emissions_csv(csv_path)

    assert result is None  # since reading the CSV fails, result should be None
    assert "Error reading file" in caplog.text


@patch("pathlib.Path.exists", return_value=False)
def test_extract_emissions_csv_missing_file(mock_exists, energy_meter, caplog):  # noqa: ARG001
    csv_path = Path("dummy_path.csv")  # fake path
    with caplog.at_level(logging.INFO):
        result = energy_meter.extract_emissions_csv(csv_path)

    assert result is None  # since file path does not exist, result should be None
    assert "File 'dummy_path.csv' does not exist." in caplog.text
