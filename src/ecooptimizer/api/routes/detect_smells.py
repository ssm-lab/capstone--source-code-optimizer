"""API endpoint for detecting code smells in Python files."""

# pyright: reportOptionalMemberAccess=false
from pathlib import Path
from fastapi import APIRouter
import time
import logging

from ecooptimizer.api.error_handler import AppError, RessourceNotFoundError

from ecooptimizer.data_types.api import SmellRequest
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.smell import Smell
from ecooptimizer.utils.load_smells import load_smells_from_file
from ecooptimizer.utils.output_manager import save_json_files

router = APIRouter()
analyzer_controller = AnalyzerController()

logger = logging.getLogger("detect")


@router.post(
    "/smells",
    response_model=list[Smell],
    summary="Detect code smells",
    response_model_exclude={"energyMetadata"},
)
def detect_smells(request: SmellRequest) -> list[Smell]:
    """Analyzes a Python file and returns detected code smells.

    Args:
        request: SmellRequest containing file path and smell configurations

    Returns:
        list[Smell]: Detected code smells with their metadata

    Raises:
        HTTPException: 404 if file not found, 500 for analysis errors
    """
    logger.info(f"{'=' * 100}")
    logger.info(f"📂 Received smell detection request for: {request.file_path}")

    start_time = time.time()

    file_path_obj = Path(request.file_path)

    if not file_path_obj.exists():
        logger.error(f"❌ File does not exist: {file_path_obj}")
        raise RessourceNotFoundError(str(file_path_obj), "file")

    try:
        logger.info(f"🎯 Running analysis on: {file_path_obj}")
        smells_data = analyzer_controller.run_analysis(file_path_obj, request.enabled_smells)

        analysis_data_file = Path(request.project_root) / "__ecocache__" / "energy_smells.json"
        analysis_data_file.parent.mkdir(parents=True, exist_ok=True)

        if analysis_data_file.exists():
            current_smell_data = load_smells_from_file(analysis_data_file)
        else:
            current_smell_data = {str(file_path_obj): {"dirty": False}}

        if str(file_path_obj) not in current_smell_data:
            current_smell_data[str(file_path_obj)] = {"dirty": False}

        current_smell_data[str(file_path_obj)]["smells"] = {
            smell.id: smell.model_dump() for smell in smells_data
        }

        save_json_files(analysis_data_file, current_smell_data)
    except AppError as e:
        raise AppError(str(e), e.status_code) from e
    except Exception as e:
        raise Exception(str(e)) from e

    execution_time = round(time.time() - start_time, 2)
    logger.info(f"📊 Execution Time: {execution_time} seconds")
    logger.info(f"🏁 Analysis completed for {file_path_obj}. {len(smells_data)} smells found.")
    logger.info(f"{'=' * 100}\n")

    return smells_data
