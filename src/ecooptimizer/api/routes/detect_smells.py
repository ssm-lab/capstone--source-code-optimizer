from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time

from ecooptimizer import OUTPUT_MANAGER
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.smell import Smell
from ...utils.smells_registry import update_smell_registry

router = APIRouter()
detect_smells_logger = OUTPUT_MANAGER.loggers["detect_smells"]
analyzer_controller = AnalyzerController()


class SmellRequest(BaseModel):
    file_path: str
    enabled_smells: list[str]


@router.post("/smells", response_model=list[Smell])
def detect_smells(request: SmellRequest):
    """
    Detects code smells in a given file, logs the process, and measures execution time.
    """

    detect_smells_logger.info(f"{'=' * 100}")
    detect_smells_logger.info(f"📂 Received smell detection request for: {request.file_path}")

    start_time = time.time()

    try:
        file_path_obj = Path(request.file_path)

        # Verify file existence
        detect_smells_logger.info(f"🔍 Checking if file exists: {file_path_obj}")
        if not file_path_obj.exists():
            detect_smells_logger.error(f"❌ File does not exist: {file_path_obj}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path_obj}")

        # Log enabled smells
        detect_smells_logger.info(
            f"🔎 Enabled smells: {', '.join(request.enabled_smells) if request.enabled_smells else 'None'}"
        )

        # Apply user preferences to the smell registry
        filter_smells(request.enabled_smells)

        # Run analysis
        detect_smells_logger.info(f"🎯 Running analysis on: {file_path_obj}")
        smells_data = analyzer_controller.run_analysis(file_path_obj)

        execution_time = round(time.time() - start_time, 2)
        detect_smells_logger.info(f"📊 Execution Time: {execution_time} seconds")

        # Log results
        detect_smells_logger.info(
            f"🏁 Analysis completed for {file_path_obj}. {len(smells_data)} smells found."
        )
        detect_smells_logger.info(f"{'=' * 100}\n")

        return smells_data

    except Exception as e:
        detect_smells_logger.error(f"❌ Error during smell detection: {e!s}")
        detect_smells_logger.info(f"{'=' * 100}\n")
        raise HTTPException(status_code=500, detail="Internal server error") from e


def filter_smells(enabled_smells: list[str]):
    """
    Updates the smell registry to reflect user-selected enabled smells.
    """
    detect_smells_logger.info("⚙️ Updating smell registry with user preferences...")
    update_smell_registry(enabled_smells)
    detect_smells_logger.info("✅ Smell registry updated successfully.")
