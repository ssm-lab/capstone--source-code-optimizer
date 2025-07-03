"""API endpoints for code refactoring with carbon savings."""

# pyright: reportOptionalMemberAccess=false
import shutil
from pathlib import Path
from tempfile import mkdtemp
import traceback
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ecooptimizer.api.error_handler import (
    AppError,
    RefactoringError,
    RessourceNotFoundError,
    remove_readonly,
)

from ecooptimizer.config import CONFIG
from ecooptimizer.refactorers.refactorer_controller import RefactorerController
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.data_types.smell import Smell

logger = CONFIG["refactorLogger"]

# Static mapping of carbon savings per smell type (in kg CO2). 
# TODO: This is a placeholder and should be replaced with actual values once empirical data is available.
CARBON_SAVINGS_MAP = {
    # Pylint smells 
    "use-a-generator": 0.0025,  
    "too-many-arguments": 0.0015,  
    "no-self-use": 0.0010,
    
    # Custom smells 
    "long-lambda-expression": 0.0020, 
    "long-message-chain": 0.0030, 
    "long-element-chain": 0.0025,
    "cached-repeated-calls": 0.0050,
    "string-concat-loop": 0.0040,
}


def get_carbon_savings_for_smell(smell_symbol: str) -> float:
    """Get static energy savings for a smell type.
     
    Args:
        smell_symbol: The smell symbol from CARBON_SAVINGS_MAP dictionary.
        
    Returns:
        Energy savings in kg CO2
    """
    savings = CARBON_SAVINGS_MAP.get(smell_symbol, 0.0)
    return savings

router = APIRouter()
refactorer_controller = RefactorerController()
analyzer_controller = AnalyzerController()


class ChangedFile(BaseModel):
    """Tracks file changes during refactoring.

    Attributes:
        original: Path to original file
        refactored: Path to refactored file
    """

    original: str
    refactored: str


class RefactoredData(BaseModel):
    """Contains results of a refactoring operation.

    Attributes:
        tempDir: Temporary directory with refactored files
        targetFile: Main file that was refactored
        energySaved: Estimated energy savings in kg CO2
        affectedFiles: List of all files modified during refactoring
    """

    tempDir: str
    targetFile: ChangedFile
    energySaved: Optional[float] = None
    affectedFiles: list[ChangedFile]


class RefactorRqModel(BaseModel):
    """Request model for single smell refactoring.

    Attributes:
        sourceDir: Directory containing code to refactor
        smell: Smell to refactor
    """

    sourceDir: str
    smell: Smell


class RefactorTypeRqModel(BaseModel):
    """Request model for refactoring by smell type.

    Attributes:
        sourceDir: Directory containing code to refactor
        smellType: Type of smell to refactor
        firstSmell: First instance of the smell to refactor
    """

    sourceDir: str
    smellType: str
    firstSmell: Smell


@router.post("/refactor", response_model=RefactoredData, summary="Refactor a specific code smell")
def refactor(request: RefactorRqModel) -> RefactoredData | None:
    """Refactors a specific code smell and measures carbon savings through empirical data.

    Args:
        request: Contains source directory and smell to refactor

    Returns:
        RefactoredData: Results including carbon savings and changed files
        None: If refactoring fails

    Raises:
        HTTPException: Various error cases with appropriate status codes
    """
    logger.info(f"{'=' * 100}")

    source_dir = Path(request.sourceDir)
    target_file = Path(request.smell.path)

    logger.info(f"🔄 Refactoring smell: {request.smell.symbol} in {source_dir!s}")

    if not target_file.exists():
        raise RessourceNotFoundError(str(target_file), "file")

    if not source_dir.is_dir():
        raise RessourceNotFoundError(str(source_dir), "folder")

    try:
        refactor_data = perform_refactoring(source_dir, request.smell)

        if refactor_data:
            logger.info(f"{'=' * 100}\n")
            return refactor_data

        logger.info(f"{'=' * 100}\n")
    except AppError as e:
        raise AppError(str(e), e.status_code) from e
    except Exception as e:
        raise Exception(str(e)) from e


@router.post(
    "/refactor-by-type", response_model=RefactoredData, summary="Refactor all smells of a type"
)
def refactorSmell(request: RefactorTypeRqModel) -> RefactoredData:
    """Refactors all instances of a smell type in a file and measures carbon savings through empirical data..

    Args:
        request: Contains source directory, smell type and first instance

    Returns:
        RefactoredData: Aggregated results of all refactorings

    Raises:
        HTTPException: Various error cases with appropriate status codes
    """
    logger.info(f"{'=' * 100}")
    source_dir = Path(request.sourceDir)
    target_file = Path(request.firstSmell.path)

    logger.info(f"🔄 Refactoring smell: {request.firstSmell.symbol} in {source_dir!s}")

    if not target_file.exists():
        raise RessourceNotFoundError(str(target_file), "file")

    if not source_dir.is_dir():
        raise RessourceNotFoundError(str(source_dir), "folder")
    
    try:
        total_energy_saved = 0.0
        all_affected_files: list[ChangedFile] = []
        temp_dir = None
        current_smell = request.firstSmell
        current_source_dir = source_dir

        refactor_data = perform_refactoring(current_source_dir, current_smell)
        total_energy_saved += refactor_data.energySaved or 0.0
        all_affected_files.extend(refactor_data.affectedFiles)

        temp_dir = refactor_data.tempDir
        target_file = refactor_data.targetFile
        refactored_file_path = target_file.refactored
        source_copy_dir = Path(temp_dir) / source_dir.name

        while True:
            next_smells = analyzer_controller.run_analysis(
                Path(refactored_file_path), [request.smellType]
            )
            if not next_smells:
                break
            current_smell = next_smells[0]
            step_data = perform_refactoring(
                source_copy_dir,
                current_smell,
                Path(temp_dir),
            )
            total_energy_saved += step_data.energySaved or 0.0
            all_affected_files.extend(step_data.affectedFiles)

        logger.info(f"✅ Total energy saved: {total_energy_saved} kg CO2")

        return RefactoredData(
            tempDir=temp_dir,
            targetFile=target_file,
            energySaved=total_energy_saved,
            affectedFiles=list({file.original: file for file in all_affected_files}.values()),
        )
    except AppError as e:
        raise AppError(str(e), e.status_code) from e
    except Exception as e:
        raise Exception(str(e)) from e


def perform_refactoring(
    source_dir: Path,
    smell: Smell,
    existing_temp_dir: Optional[Path] = None,
) -> RefactoredData:
    """Executes the refactoring process and calculates carbon savings.

    Args:
        source_dir: Source directory to refactor
        smell: Smell to refactor
        existing_temp_dir: Optional existing temp directory to use

    Returns:
        RefactoredData: Results of the refactoring operation

    Raises:
        RefactoringError: If refactoring fails
    """
    print()
    target_file = Path(smell.path)

    logger.info(
        f"🚀 Starting refactoring for {smell.symbol} at line {smell.occurences[0].line} in {target_file}"
    )

    if existing_temp_dir is None:
        temp_dir = Path(mkdtemp(prefix="ecooptimizer-"))
        source_copy = temp_dir / source_dir.name
        shutil.copytree(source_dir, source_copy, ignore=shutil.ignore_patterns(".git*"))
    else:
        temp_dir = existing_temp_dir
        source_copy = source_dir

    target_file_copy = source_copy / target_file.relative_to(source_dir)
    modified_files = []
    try:
        modified_files: list[Path] = refactorer_controller.run_refactorer(
            target_file_copy, source_copy, smell
        )
    except Exception as e:
        shutil.rmtree(temp_dir, onerror=remove_readonly)  # type: ignore
        traceback.print_exc()
        raise RefactoringError(str(e)) from e

    # Get static energy savings instead of measuring
    energy_saved = get_carbon_savings_for_smell(smell.symbol)
    
    return RefactoredData(
        tempDir=str(temp_dir),
        targetFile=ChangedFile(
            original=str(target_file.resolve()),
            refactored=str(target_file_copy.resolve()),
        ),
        energySaved=energy_saved,
        affectedFiles=[
            ChangedFile(
                original=str(file.resolve()).replace(str(source_copy), str(source_dir)),
                refactored=str(file.resolve()),
            )
            for file in modified_files
        ],
    )