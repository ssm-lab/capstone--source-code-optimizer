# pyright: reportOptionalMemberAccess=false
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time

from ...config import CONFIG

from ...analyzers.analyzer_controller import AnalyzerController
from ...data_types.smell import Smell
from ...utils.smells_registry import update_smell_registry

router = APIRouter()

analyzer_controller = AnalyzerController()


class SmellRequest(BaseModel):
    file_path: str
    enabled_smells: list[str]


@router.post("/smells", response_model=list[Smell])
def detect_smells(request: SmellRequest):
    """
    Detects code smells in a given file, logs the process, and measures execution time.
    """

    print(CONFIG["detectLogger"])
    CONFIG["detectLogger"].info(f"{'=' * 100}")
    CONFIG["detectLogger"].info(f"📂 Received smell detection request for: {request.file_path}")

    start_time = time.time()

    try:
        file_path_obj = Path(request.file_path)

        # Verify file existence
        CONFIG["detectLogger"].info(f"🔍 Checking if file exists: {file_path_obj}")
        if not file_path_obj.exists():
            CONFIG["detectLogger"].error(f"❌ File does not exist: {file_path_obj}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path_obj}")

        # Log enabled smells
        CONFIG["detectLogger"].info(
            f"🔎 Enabled smells: {', '.join(request.enabled_smells) if request.enabled_smells else 'None'}"
        )

        # Apply user preferences to the smell registry
        filter_smells(request.enabled_smells)

        # Run analysis
        CONFIG["detectLogger"].info(f"🎯 Running analysis on: {file_path_obj}")
        smells_data = analyzer_controller.run_analysis(file_path_obj)

        execution_time = round(time.time() - start_time, 2)
        CONFIG["detectLogger"].info(f"📊 Execution Time: {execution_time} seconds")

        # Log results
        CONFIG["detectLogger"].info(
            f"🏁 Analysis completed for {file_path_obj}. {len(smells_data)} smells found."
        )
        CONFIG["detectLogger"].info(f"{'=' * 100}\n")

        return smells_data

    except Exception as e:
        CONFIG["detectLogger"].error(f"❌ Error during smell detection: {e!s}")
        CONFIG["detectLogger"].info(f"{'=' * 100}\n")
        raise HTTPException(status_code=500, detail="Internal server error") from e


def filter_smells(enabled_smells: list[str]):
    """
    Updates the smell registry to reflect user-selected enabled smells.
    """
    CONFIG["detectLogger"].info("⚙️ Updating smell registry with user preferences...")
    update_smell_registry(enabled_smells)
    CONFIG["detectLogger"].info("✅ Smell registry updated successfully.")
