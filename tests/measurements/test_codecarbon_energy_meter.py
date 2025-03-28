import math
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd
import subprocess

from ecooptimizer.measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter


@pytest.fixture
def mock_dependencies():
    """Fixture to mock all dependencies with proper subprocess mocking"""
    with (
        patch("subprocess.run") as mock_subprocess,
        patch("ecooptimizer.measurements.codecarbon_energy_meter.EmissionsTracker") as mock_tracker,
        patch(
            "ecooptimizer.measurements.codecarbon_energy_meter.TemporaryDirectory"
        ) as mock_tempdir,
        patch.object(Path, "exists") as mock_exists,
        patch.object(CodeCarbonEnergyMeter, "_extract_emissions_data"),
    ):
        # Setup default successful subprocess mock
        process_mock = MagicMock()
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Setup tracker mock
        tracker_instance = MagicMock()
        mock_tracker.return_value = tracker_instance

        # Setup tempdir mock
        mock_tempdir.return_value.__enter__.return_value = "/fake/temp/dir"

        mock_exists.return_value = True

        yield {
            "subprocess": mock_subprocess,
            "tracker": mock_tracker,
            "tracker_instance": tracker_instance,
            "tempdir": mock_tempdir,
            "exists": mock_exists,
        }


class TestCodeCarbonEnergyMeter:
    @pytest.fixture
    def meter(self):
        return CodeCarbonEnergyMeter()

    def test_measure_energy_success(self, meter, mock_dependencies):
        """Test successful measurement with float return value."""
        mock_dependencies["tracker_instance"].stop.return_value = 1.23

        test_file = Path("test.py")
        meter.measure_energy(test_file)

        assert meter.emissions == 1.23
        mock_dependencies["subprocess"].assert_called_once()
        mock_dependencies["tracker_instance"].start.assert_called_once()
        mock_dependencies["tracker_instance"].stop.assert_called_once()

    def test_measure_energy_none_return(self, meter, mock_dependencies):
        """Test measurement that returns None."""
        mock_dependencies["tracker_instance"].stop.return_value = None

        test_file = Path("test.py")
        meter.measure_energy(test_file)

        assert meter.emissions is None
        mock_dependencies["tracker_instance"].stop.assert_called_once()

    def test_measure_energy_unexpected_return_type(self, meter, mock_dependencies, caplog):
        """Test handling of unexpected return types."""
        mock_dependencies["tracker_instance"].stop.return_value = "invalid"

        test_file = Path("test.py")
        meter.measure_energy(test_file)

        assert meter.emissions is None
        assert "Unexpected emissions type" in caplog.text
        mock_dependencies["tracker_instance"].stop.assert_called_once()

    def test_measure_energy_nan_return_type(self, meter, mock_dependencies, caplog):
        """Test handling of unexpected return types."""
        mock_dependencies["tracker_instance"].stop.return_value = math.nan

        test_file = Path("test.py")
        meter.measure_energy(test_file)

        assert meter.emissions is None
        assert "Unexpected emissions type" in caplog.text
        mock_dependencies["tracker_instance"].stop.assert_called_once()

    def test_measure_energy_subprocess_failure(
        self, meter, mock_dependencies: dict[str, MagicMock], caplog
    ):
        """Test handling of subprocess failures."""
        # Configure subprocess to raise error
        mock_dependencies["subprocess"].side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["python", "test.py"], output="Error output", stderr="Error details"
        )
        mock_dependencies["tracker_instance"].stop.return_value = 1.23

        test_file = Path("test.py")
        meter.measure_energy(test_file)

        mock_dependencies["subprocess"].assert_called()
        assert "Error executing file" in caplog.text
        assert meter.emissions == 1.23

    def test_extract_emissions_data_success(self, meter, tmp_path):
        """Test successful extraction of emissions data."""
        test_data = [
            {"timestamp": "2023-01-01", "emissions": 1.0},
            {"timestamp": "2023-01-02", "emissions": 2.0},
        ]
        df = pd.DataFrame(test_data)
        csv_path = tmp_path / "emissions.csv"
        df.to_csv(csv_path, index=False)

        result = meter._extract_emissions_data(csv_path)
        assert result == test_data[-1]

    def test_extract_emissions_data_failure(self, meter, tmp_path, caplog):
        """Test failure to extract emissions data."""
        csv_path = tmp_path / "nonexistent.csv"
        result = meter._extract_emissions_data(csv_path)

        assert result is None
        assert "Failed to read emissions data" in caplog.text

    def test_measure_energy_missing_emissions_file(self, meter, mock_dependencies, caplog):
        """Test handling when emissions file is missing."""
        mock_dependencies["tracker_instance"].stop.return_value = 1.23
        mock_dependencies["exists"].return_value = False

        with patch.object(Path, "exists", return_value=False):
            test_file = Path("test.py")
            meter.measure_energy(test_file)

            assert "Emissions file missing" in caplog.text
            assert meter.emissions_data is None
