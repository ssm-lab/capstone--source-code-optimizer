"""API endpoints for code refactoring with energy measurement."""

# pyright: reportOptionalMemberAccess=false
import logging
import shutil
from pathlib import Path
from tempfile import mkdtemp
import traceback
from fastapi import APIRouter

from ecooptimizer.api.error_handler import (
    AppError,
    RefactoringError,
    RessourceNotFoundError,
    remove_readonly,
)

from ecooptimizer.data_types.api import ChangedFile, RefactorRqModel, RefactoredData
from ecooptimizer.refactorers.refactorer_controller import RefactorerController
from ecooptimizer.analyzers.analyzer_controller import AnalyzerController
from ecooptimizer.measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
from ecooptimizer.data_types.smell import Smell
from ecooptimizer.refactorers.utils.smell_mapper import (
    adjust_modified_files,
)
from ecooptimizer.utils.load_smells import load_smells_from_file

logger = logging.getLogger("refactor")

router = APIRouter()
refactorer_controller = RefactorerController()
analyzer_controller = AnalyzerController()
energy_meter = CodeCarbonEnergyMeter()


@router.post("/refactor", response_model=RefactoredData, summary="Refactor a specific code smell")
def refactor(request: RefactorRqModel) -> RefactoredData | None:
    """Refactors a specific code smell and measures energy impact.

    Args:
        request: Contains source directory and smell to refactor

    Returns:
        RefactoredData: Results including energy savings and changed files
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
        if not request.smell:
            raise AttributeError(
                "Missing smell parameter in request. Smell param is necessary for refactory singular smells."
            )
        analysis_data_file = source_dir / "__ecocache__" / "energy_smells.json"
        updated_data_file = source_dir / "__ecocache__" / "energy_smells.updated.json"

        if updated_data_file.exists():
            data_file = updated_data_file
        else:
            data_file = analysis_data_file

        refactor_data = perform_refactoring(source_dir, request.smell)

        adjust_modified_files(
            refactor_data.affectedFiles, source_dir, data_file, request.smell, temp=True
        )

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
def refactorType(request: RefactorRqModel) -> RefactoredData:
    """Refactors all instances of a smell type in a file.

    Args:
        request: Contains source directory, smell type and first instance

    Returns:
        RefactoredData: Aggregated results of all refactorings

    Raises:
        HTTPException: Various error cases with appropriate status codes
    """
    logger.info(f"{'=' * 100}")
    source_dir = Path(request.sourceDir)

    if not request.targetFile:
        raise AttributeError(
            "Missing targetFile parameter in request. targetFile param is necessary for refactory smell types."
        )

    if not request.smellType:
        raise AttributeError(
            "Missing smellType parameter in request. smellType param is necessary for refactory smell types."
        )
    target_path = Path(request.targetFile)

    logger.info(f"🔄 Refactoring smell: {request.smellType} in {target_path!s}")

    if not target_path.exists():
        raise RessourceNotFoundError(str(target_path), "file")

    if not source_dir.is_dir():
        raise RessourceNotFoundError(str(source_dir), "folder")
    try:
        all_affected_files: list[ChangedFile] = []
        root = source_dir
        target_file = None

        analysis_data_file = source_dir / "__ecocache__" / "energy_smells.json"
        updated_data_file = source_dir / "__ecocache__" / "energy_smells.updated.json"
        temp_data_file = source_dir / "__ecocache__" / "energy_smells.temp.json"

        if updated_data_file.exists():
            data_file = updated_data_file
        else:
            data_file = analysis_data_file

        smells_to_refactor = load_smells_from_file(analysis_data_file)[request.targetFile]["smells"]

        using_temp = False
        while smells_to_refactor:
            smell = Smell(
                **smells_to_refactor.get(
                    next(
                        key
                        for key in smells_to_refactor.keys()
                        if smells_to_refactor[key]["symbol"] == request.smellType
                    ),
                    {},
                )
            )

            step_data = perform_refactoring(
                source_dir,
                smell,
                root if using_temp else None,
            )

            target_file = step_data.targetFile
            all_affected_files.extend(step_data.affectedFiles)

            adjust_modified_files(step_data.affectedFiles, source_dir, data_file, smell, temp=True)

            smells_to_refactor = load_smells_from_file(analysis_data_file)[request.targetFile][
                "smells"
            ]

            if not using_temp:
                root = Path(step_data.tempDir) / source_dir.name
                data_file = temp_data_file
                using_temp = True

        print("All smell refactored succesfully")

        return RefactoredData(
            tempDir=str(root),
            targetFile=target_file,
            affectedFiles=list({file.original: file for file in all_affected_files}.values()),
        )
    except AppError as e:
        raise AppError(str(e), e.status_code) from e
    except Exception as e:
        raise Exception(str(e)) from e


@router.post("/refactor-all", response_model=RefactoredData, summary="Refactor all smells")
def refactorAll(request: RefactorRqModel) -> RefactoredData:
    """Refactors all instances of a smells in a file.

    Args:
        request: Contains source directory and file to be refactored

    Returns:
        RefactoredData: Aggregated results of all refactorings

    Raises:
        HTTPException: Various error cases with appropriate status codes
    """
    logger.info(f"{'=' * 100}")
    source_dir = Path(request.sourceDir)

    if not request.targetFile:
        raise AttributeError(
            "Missing targetFile parameter in request. targetFile param is necessary for refactoring all smells."
        )

    target_path = Path(request.targetFile)

    logger.info(f"🔄 Refactoring smells in {target_path!s}")

    if not target_path.exists():
        raise RessourceNotFoundError(str(target_path), "file")

    if not source_dir.is_dir():
        raise RessourceNotFoundError(str(source_dir), "folder")
    try:
        all_affected_files: list[ChangedFile] = []
        root = source_dir
        target_file = None

        analysis_data_file = source_dir / "__ecocache__" / "energy_smells.json"
        updated_data_file = source_dir / "__ecocache__" / "energy_smells.updated.json"
        temp_data_file = source_dir / "__ecocache__" / "energy_smells.temp.json"

        if updated_data_file.exists():
            data_file = updated_data_file
        else:
            data_file = analysis_data_file

        smells_to_refactor = load_smells_from_file(analysis_data_file)[request.targetFile]["smells"]

        using_temp = False
        while smells_to_refactor:
            smell = Smell(
                **smells_to_refactor.get(
                    next(key for key in smells_to_refactor.keys()),
                    {},
                )
            )

            try:
                step_data = perform_refactoring(
                    source_dir,
                    smell,
                    root if using_temp else None,
                )

                target_file = step_data.targetFile
                all_affected_files.extend(step_data.affectedFiles)

                adjust_modified_files(
                    step_data.affectedFiles, source_dir, data_file, smell, temp=True
                )

            except Exception:
                logger.debug(
                    f"Refactoring failed for smell {smell.id} at {smell.path}, skipping..."
                )
                print(f"Refactoring failed for smell {smell.id} at {smell.path}, skipping...")
            finally:
                if not using_temp:
                    root = Path(step_data.tempDir) / source_dir.name
                    data_file = temp_data_file
                    using_temp = True

                smells_to_refactor = load_smells_from_file(data_file)[request.targetFile]["smells"]

        print("All smell refactored succesfully")

        return RefactoredData(
            tempDir=str(root),
            targetFile=target_file,
            affectedFiles=list({file.original: file for file in all_affected_files}.values()),
        )
    except AppError as e:
        raise AppError(str(e), e.status_code) from e
    except Exception as e:
        raise Exception(str(e)) from e


def perform_refactoring(
    source_dir: Path,
    smell: Smell,
    existing_temp_dir: Path | None = None,
) -> RefactoredData:
    """Executes the refactoring process and measures energy impact.

    Args:
        sourceDir: Source directory to refactor
        smell: Smell to refactor
        initial_emissions: Baseline energy measurement
        existing_temp_dir: Optional existing temp directory to use

    Returns:
        RefactoredData: Results of the refactoring operation

    Raises:
        RuntimeError: If energy measurement fails
        EnergySavingsError: If refactoring doesn't save energy
        RefactoringError: If refactoring fails
    """
    print()
    target_file = Path(smell.path)

    logger.info(
        f"🚀 Starting refactoring for {smell.symbol} at line {smell.occurences[0].line} in {target_file}"
    )

    if existing_temp_dir is None:
        temp_dir = Path(mkdtemp(prefix="ecooptimizer-"))
        print("Temp dir created:", temp_dir, "exists?", temp_dir.exists())

        print("Source dir:", source_dir, "exists?", source_dir.exists())

        source_copy = temp_dir / source_dir.name
        print("Destination will be:", source_copy)

        shutil.copytree(source_dir, source_copy, ignore=shutil.ignore_patterns(".git*"))
        print("Copied? Exists:", source_copy.exists())
    else:
        temp_dir = existing_temp_dir.parent
        source_copy = temp_dir / source_dir.name

    logger.debug(f"Source: {source_dir}, copied to temporary directory at {source_copy}")
    root_idx = target_file.parts.index(source_dir.name)
    target_file_copy = source_copy / Path(*target_file.parts[root_idx + 2 :])

    logger.debug(f"Target file copy located at {target_file_copy}")
    modified_files = []
    try:
        modified_files: list[Path] = refactorer_controller.run_refactorer(
            target_file_copy, source_copy, smell
        )
        logger.debug(f"Modified files: {[str(file) for file in modified_files]}")
    except Exception as e:
        # shutil.rmtree(temp_dir, onerror=remove_readonly)  # type: ignore
        traceback.print_exc()
        raise RefactoringError(str(e)) from e

    return RefactoredData(
        tempDir=str(temp_dir),
        targetFile=ChangedFile(
            original=str(target_file.resolve()),
            refactored=str(target_file_copy.resolve()),
        ),
        affectedFiles=[
            ChangedFile(
                original=str(file.resolve()).replace(str(source_copy), str(source_dir)),
                refactored=str(file.resolve()),
            )
            for file in modified_files
        ],
    )
