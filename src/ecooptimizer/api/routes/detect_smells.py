"""API endpoint for detecting code smells in Python files."""

# pyright: reportOptionalMemberAccess=false
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
import time

from ecooptimizer.api.error_handler import AppError, RessourceNotFoundError

from ecooptimizer.config import CONFIG
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.smell import Smell

router = APIRouter()
analyzer_controller = AnalyzerController()


class SmellRequest(BaseModel):
    """Request model for smell detection endpoint.

    Attributes:
        file_path: Path to the Python file to analyze
        enabled_smells: Dictionary mapping smell names to their configurations
    """

    file_path: str
    enabled_smells: dict[str, dict[str, int | str]]


@router.post("/smells", response_model=list[Smell], summary="Detect code smells")
def detect_smells(request: SmellRequest) -> list[Smell]:
    """Analyzes a Python file and returns detected code smells.

    Args:
        request: SmellRequest containing file path and smell configurations

    Returns:
        list[Smell]: Detected code smells with their metadata

    Raises:
        HTTPException: 404 if file not found, 500 for analysis errors
    """
    CONFIG["detectLogger"].info(f"{'=' * 100}")
    CONFIG["detectLogger"].info(f"📂 Received smell detection request for: {request.file_path}")

    start_time = time.time()

    file_path_obj = Path(request.file_path)

    if not file_path_obj.exists():
        CONFIG["detectLogger"].error(f"❌ File does not exist: {file_path_obj}")
        raise RessourceNotFoundError(str(file_path_obj), "file")

    try:
        CONFIG["detectLogger"].info(f"🎯 Running analysis on: {file_path_obj}")
        smells_data = analyzer_controller.run_analysis(file_path_obj, request.enabled_smells)
    except AppError as e:
        raise AppError(str(e), e.status_code) from e
    except Exception as e:
        raise Exception(str(e)) from e

    execution_time = round(time.time() - start_time, 2)
    CONFIG["detectLogger"].info(f"📊 Execution Time: {execution_time} seconds")
    CONFIG["detectLogger"].info(
        f"🏁 Analysis completed for {file_path_obj}. {len(smells_data)} smells found."
    )
    CONFIG["detectLogger"].info(f"{'=' * 100}\n")

    return smells_data
