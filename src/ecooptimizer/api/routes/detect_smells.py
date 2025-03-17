# pyright: reportOptionalMemberAccess=false
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time

from ...config import CONFIG

from ...analyzers.analyzer_controller import AnalyzerController
from ...data_types.smell import Smell

router = APIRouter()

analyzer_controller = AnalyzerController()


class SmellRequest(BaseModel):
    file_path: str
    enabled_smells: dict[str, dict[str, int | str]]  # ✅ Dictionary for smell options


@router.post("/smells", response_model=list[Smell])
def detect_smells(request: SmellRequest):
    """
    Detects code smells in a given file, logs the process, and measures execution time.
    """

    CONFIG["detectLogger"].info(f"{'=' * 100}")
    CONFIG["detectLogger"].info(f"📂 Received smell detection request for: {request.file_path}")

    start_time = time.time()

    try:
        file_path_obj = Path(request.file_path)
        enabled_smells = request.enabled_smells

        if not file_path_obj.exists():
            CONFIG["detectLogger"].error(f"❌ File does not exist: {file_path_obj}")
            raise FileNotFoundError(f"File not found: {file_path_obj}")

        if not isinstance(enabled_smells, dict):
            CONFIG["detectLogger"].error(
                f"❌ Invalid enabled_smells format: {type(enabled_smells)}"
            )
            raise TypeError("enabled_smells must be a dictionary.")

        # Run analysis
        CONFIG["detectLogger"].info(f"🎯 Running analysis on: {file_path_obj}")
        smells_data = analyzer_controller.run_analysis(file_path_obj, request.enabled_smells)

        execution_time = round(time.time() - start_time, 2)
        CONFIG["detectLogger"].info(f"📊 Execution Time: {execution_time} seconds")

        CONFIG["detectLogger"].info(
            f"🏁 Analysis completed for {file_path_obj}. {len(smells_data)} smells found."
        )
        CONFIG["detectLogger"].info(f"{'=' * 100}\n")

        return smells_data

    except FileNotFoundError as e:
        CONFIG["detectLogger"].error(f"❌ File not found: {e}")
        CONFIG["detectLogger"].info(f"{'=' * 100}\n")
        raise HTTPException(status_code=404, detail=str(e)) from e

    except Exception as e:
        CONFIG["detectLogger"].error(f"❌ Error during smell detection: {e!s}")
        CONFIG["detectLogger"].info(f"{'=' * 100}\n")
        raise HTTPException(status_code=500, detail="Internal server error") from e
