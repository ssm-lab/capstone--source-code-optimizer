import shutil
import math
from pathlib import Path
from tempfile import mkdtemp
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from ... import OUTPUT_MANAGER
from ...analyzers.analyzer_controller import AnalyzerController
from ...exceptions import EnergySavingsError, RefactoringError
from ...refactorers.refactorer_controller import RefactorerController
from ...measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from ...data_types.smell import Smell

router = APIRouter()
refactor_logger = OUTPUT_MANAGER.loggers["refactor_smell"]
analyzer_controller = AnalyzerController()
refactorer_controller = RefactorerController()


class ChangedFile(BaseModel):
    original: str
    refactored: str


class RefactoredData(BaseModel):
    tempDir: str
    targetFile: ChangedFile
    energySaved: Optional[float] = None
    affectedFiles: list[ChangedFile]


class RefactorRqModel(BaseModel):
    source_dir: str
    smell: Smell


class RefactorResModel(BaseModel):
    refactoredData: Optional[RefactoredData] = None
    updatedSmells: list[Smell]


@router.post("/refactor", response_model=RefactorResModel)
def refactor(request: RefactorRqModel):
    """Handles the refactoring process for a given smell."""
    refactor_logger.info(f"{'=' * 100}")
    refactor_logger.info("🔄 Received refactor request.")

    try:
        refactor_logger.info(f"🔍 Analyzing smell: {request.smell.symbol} in {request.source_dir}")
        refactor_data, updated_smells = perform_refactoring(Path(request.source_dir), request.smell)

        refactor_logger.info(
            f"✅ Refactoring process completed. Updated smells: {len(updated_smells)}"
        )

        if refactor_data:
            refactor_data = clean_refactored_data(refactor_data)
            refactor_logger.info(f"{'=' * 100}\n")
            return RefactorResModel(refactoredData=refactor_data, updatedSmells=updated_smells)

        refactor_logger.info(f"{'=' * 100}\n")
        return RefactorResModel(updatedSmells=updated_smells)

    except Exception as e:
        refactor_logger.error(f"❌ Refactoring error: {e!s}")
        refactor_logger.info(f"{'=' * 100}\n")
        raise HTTPException(status_code=400, detail=str(e)) from e


def perform_refactoring(source_dir: Path, smell: Smell):
    """Executes the refactoring process for a given smell."""
    target_file = Path(smell.path)

    refactor_logger.info(
        f"🚀 Starting refactoring for {smell.symbol} at line {smell.occurences[0].line} in {target_file}"
    )

    if not source_dir.is_dir():
        refactor_logger.error(f"❌ Directory does not exist: {source_dir}")
        raise OSError(f"Directory {source_dir} does not exist.")

    energy_meter = CodeCarbonEnergyMeter()
    energy_meter.measure_energy(target_file)
    initial_emissions = energy_meter.emissions

    if not initial_emissions:
        refactor_logger.error("❌ Could not retrieve initial emissions.")
        raise RuntimeError("Could not retrieve initial emissions.")

    refactor_logger.info(f"📊 Initial emissions: {initial_emissions} kg CO2")

    temp_dir = mkdtemp(prefix="ecooptimizer-")
    source_copy = Path(temp_dir) / source_dir.name
    target_file_copy = Path(str(target_file).replace(str(source_dir), str(source_copy), 1))

    shutil.copytree(source_dir, source_copy)

    modified_files = []
    try:
        modified_files: list[Path] = refactorer_controller.run_refactorer(
            target_file_copy, source_copy, smell
        )
    except NotImplementedError:
        print("Not implemented yet.")
    except Exception as e:
        print(f"An unexpected error occured: {e!s}")
        traceback.print_exc()
        shutil.rmtree(temp_dir)
        raise RefactoringError(str(target_file), str(e)) from e

    energy_meter.measure_energy(target_file_copy)
    final_emissions = energy_meter.emissions

    if not final_emissions:
        print("❌ Could not retrieve final emissions. Discarding refactoring.")
        refactor_logger.error("❌ Could not retrieve final emissions. Discarding refactoring.")
        shutil.rmtree(temp_dir)
        raise RuntimeError("Could not retrieve initial emissions.")

    if final_emissions >= initial_emissions:
        refactor_logger.info(f"📊 Final emissions: {final_emissions} kg CO2")
        refactor_logger.info("⚠️ No measured energy savings. Discarding refactoring.")
        print("❌ Could not retrieve final emissions. Discarding refactoring.")
        shutil.rmtree(temp_dir)
        raise EnergySavingsError(str(target_file), "Energy was not saved after refactoring.")

    refactor_logger.info(f"✅ Energy saved! Initial: {initial_emissions}, Final: {final_emissions}")

    refactor_data = {
        "tempDir": temp_dir,
        "targetFile": {
            "original": str(target_file.resolve()),
            "refactored": str(target_file_copy.resolve()),
        },
        "energySaved": initial_emissions - final_emissions
        if not math.isnan(initial_emissions - final_emissions)
        else None,
        "affectedFiles": [
            {
                "original": str(file.resolve()).replace(
                    str(source_copy.resolve()), str(source_dir.resolve())
                ),
                "refactored": str(file.resolve()),
            }
            for file in modified_files
        ],
    }

    updated_smells = analyzer_controller.run_analysis(target_file_copy)
    return refactor_data, updated_smells


def clean_refactored_data(refactor_data: dict[str, Any]):
    """Ensures the refactored data is correctly structured and handles missing fields."""
    try:
        return RefactoredData(
            tempDir=refactor_data.get("tempDir", ""),
            targetFile=ChangedFile(
                original=refactor_data["targetFile"].get("original", ""),
                refactored=refactor_data["targetFile"].get("refactored", ""),
            ),
            energySaved=refactor_data.get("energySaved", None),
            affectedFiles=[
                ChangedFile(
                    original=file.get("original", ""),
                    refactored=file.get("refactored", ""),
                )
                for file in refactor_data.get("affectedFiles", [])
            ],
        )
    except KeyError as e:
        refactor_logger.error(f"❌ Missing expected key in refactored data: {e}")
        raise HTTPException(status_code=500, detail=f"Missing key: {e}") from e
