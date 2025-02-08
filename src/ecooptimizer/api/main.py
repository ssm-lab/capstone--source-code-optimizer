import logging
import shutil
from tempfile import mkdtemp
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..testing.test_runner import TestRunner
import math
from typing import Optional
from ..refactorers.refactorer_controller import RefactorerController

from ..analyzers.analyzer_controller import AnalyzerController

from ..data_types.smell import Smell
from ..measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter

from .. import OUTPUT_MANAGER, OUTPUT_DIR

outputs_dir = Path("/Users/tanveerbrar/Desktop").resolve()
app = FastAPI()

analyzer_controller = AnalyzerController()
refactorer_controller = RefactorerController(OUTPUT_DIR)


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
    refactoredData: RefactoredData = None  # type: ignore
    updatedSmells: list[Smell]


def replace_nan_with_null(data: any):
    if isinstance(data, float) and math.isnan(data):
        return None
    elif isinstance(data, dict):
        return {k: replace_nan_with_null(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_nan_with_null(item) for item in data]

    else:
        return data


@app.get("/smells", response_model=list[Smell])
def get_smells(file_path: str):
    try:
        smells = detect_smells(Path(file_path))
        OUTPUT_MANAGER.save_json_files(
            "returned_smells.json",
            [smell.model_dump() for smell in smells],
        )
        return smells
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/refactor")
def refactor(request: RefactorRqModel):
    try:
        print(request.model_dump_json())
        refactor_data, updated_smells = testing_refactor_smell(
            Path(request.source_dir),
            request.smell,
        )
        refactor_data = replace_nan_with_null(refactor_data)
        if not refactor_data:
            return RefactorResModel(updatedSmells=updated_smells)
        else:
            print(refactor_data.model_dump_json())
            return RefactorResModel(refactoredData=refactor_data, updatedSmells=updated_smells)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/refactorAll")
def refactor_all(request: RefactorRqModel):
    try:
        print(request.model_dump_json())

        # run once to get our varibales initialized top use again
        refactor_data, updated_smells = refactor_each_smell_for_type(
            Path(request.source_dir),
            request.smell,
        )

        if not refactor_data:
            return RefactorResModel(updatedSmells=updated_smells)

        count = 0

        # keep refactoring until updated smells doesnt contain our smeel type
        while any(smell.messageId == request.smell.messageId for smell in updated_smells):
            count += 1
            logging.info(f"Refactoring again: {count}")
            smell_to_refactor = next(
                smell for smell in updated_smells if smell.messageId == request.smell.messageId
            )
            logging.info(f"refactoring line: {smell_to_refactor.occurences[0].line}")

            refactor_data, updated_smells = refactor_each_smell_for_type(
                Path(refactor_data.tempDir),
                smell_to_refactor,
            )

        refactor_data, updated_smells = measure_energy_savings(
            request.smell, refactor_data, updated_smells
        )

        refactor_data = replace_nan_with_null(refactor_data)
        if not refactor_data:
            return RefactorResModel(updatedSmells=updated_smells)
        else:
            print(refactor_data.model_dump_json())
            return RefactorResModel(refactoredData=refactor_data, updatedSmells=updated_smells)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


def detect_smells(file_path: Path) -> list[Smell]:
    """
    Detect code smells in a given file.

    Args:
        file_path (Path): Path to the Python file to analyze.

    Returns:
        List[Smell]: A list of detected smells.
    """
    logging.info(f"Starting smell detection for file: {file_path}")

    if not file_path.is_file():
        logging.error(f"File {file_path} does not exist.")

        raise FileNotFoundError(f"File {file_path} does not exist.")

    smells_data = analyzer_controller.run_analysis(file_path)

    OUTPUT_MANAGER.save_json_files(
        "code_smells.json",
        [smell.model_dump() for smell in smells_data],
    )

    logging.info(f"Detected {len(smells_data)} code smells.")

    return smells_data


# FOR TESTING PLUGIN ONLY
def testing_refactor_smell(source_dir: Path, smell: Smell):
    targetFile = smell.path

    logging.info(
        f"Starting refactoring for smell symbol: {smell.symbol}\
          at line {smell.occurences[0].line} in file: {targetFile}"
    )

    if not source_dir.is_dir():
        logging.error(f"Directory {source_dir} does not exist.")

        raise OSError(f"Directory {source_dir} does not exist.")

    # Measure initial energy
    energy_meter = CodeCarbonEnergyMeter()
    energy_meter.measure_energy(Path(targetFile))
    initial_emissions = energy_meter.emissions

    if not initial_emissions:
        logging.error("Could not retrieve initial emissions.")
        raise RuntimeError("Could not retrieve initial emissions.")

    logging.info(f"Initial emissions: {initial_emissions}")

    refactor_data = None
    updated_smells = []

    tempDir = Path(mkdtemp(prefix="ecooptimizer-"))

    source_copy = tempDir / source_dir.name
    target_file_copy = Path(targetFile.replace(str(source_dir), str(source_copy), 1))

    # source_copy = project_copy / SOURCE.name

    shutil.copytree(source_dir, source_copy)

    try:
        modified_files: list[Path] = refactorer_controller.run_refactorer(
            target_file_copy, source_copy, smell
        )
    except NotImplementedError as e:
        raise RuntimeError(str(e)) from e

    energy_meter.measure_energy(target_file_copy)
    final_emissions = energy_meter.emissions

    if not final_emissions:
        logging.error("Could not retrieve final emissions. Discarding refactoring.")
        print("Refactoring Failed.\n")
        shutil.rmtree(tempDir)
    else:
        logging.info(f"Initial emissions: {initial_emissions} | Final emissions: {final_emissions}")

        print("Refactoring Succesful!\n")

        refactor_data = RefactoredData(
            tempDir=str(tempDir.resolve()),
            targetFile=ChangedFile(
                original=str(Path(smell.path).resolve()),
                refactored=str(target_file_copy.resolve()),
            ),
            energySaved=(
                None
                if math.isnan(final_emissions - initial_emissions)
                else (final_emissions - initial_emissions)
            ),
            affectedFiles=[
                ChangedFile(
                    original=str(file.resolve()).replace(
                        str(source_copy.resolve()), str(source_dir.resolve())
                    ),
                    refactored=str(file.resolve()),
                )
                for file in modified_files
            ],
        )

        updated_smells = detect_smells(target_file_copy)

    return refactor_data, updated_smells


def refactor_smell(source_dir: Path, smell: Smell):
    targetFile = smell.path

    logging.info(
        f"Starting refactoring for smell symbol: {smell.symbol}\
          at line {smell.occurences[0].line} in file: {targetFile}"
    )

    if not source_dir.is_dir():
        logging.error(f"Directory {source_dir} does not exist.")

        raise OSError(f"Directory {source_dir} does not exist.")

    # Measure initial energy
    energy_meter = CodeCarbonEnergyMeter()
    energy_meter.measure_energy(Path(targetFile))
    initial_emissions = energy_meter.emissions

    if not initial_emissions:
        logging.error("Could not retrieve initial emissions.")
        raise RuntimeError("Could not retrieve initial emissions.")

    logging.info(f"Initial emissions: {initial_emissions}")

    refactor_data = None
    updated_smells = []

    tempDir = Path(mkdtemp(prefix="ecooptimizer-"))

    source_copy = tempDir / source_dir.name
    target_file_copy = Path(targetFile.replace(str(source_dir), str(source_copy), 1))

    # source_copy = project_copy / SOURCE.name

    shutil.copytree(source_dir, source_copy)

    try:
        modified_files: list[Path] = refactorer_controller.run_refactorer(
            target_file_copy, source_copy, smell
        )
    except NotImplementedError as e:
        raise RuntimeError(str(e)) from e

    energy_meter.measure_energy(target_file_copy)
    final_emissions = energy_meter.emissions

    if not final_emissions:
        logging.error("Could not retrieve final emissions. Discarding refactoring.")
        print("Refactoring Failed.\n")
        shutil.rmtree(tempDir)

    elif final_emissions >= initial_emissions:
        logging.info("No measured energy savings. Discarding refactoring.\n")
        print("Refactoring Failed.\n")
        shutil.rmtree(tempDir)

    else:
        logging.info("Energy saved!")
        logging.info(f"Initial emissions: {initial_emissions} | Final emissions: {final_emissions}")

        if not TestRunner("pytest", Path(tempDir)).retained_functionality():
            logging.info("Functionality not maintained. Discarding refactoring.\n")
            print("Refactoring Failed.\n")

        else:
            logging.info("Functionality maintained! Retaining refactored file.\n")
            print("Refactoring Succesful!\n")

            refactor_data = RefactoredData(
                tempDir=str(tempDir),
                targetFile=ChangedFile(original=smell.path, refactored=str(target_file_copy)),
                energySaved=(
                    None
                    if math.isnan(final_emissions - initial_emissions)
                    else (final_emissions - initial_emissions)
                ),
                affectedFiles=[
                    ChangedFile(
                        original=str(file).replace(str(source_copy), str(source_dir)),
                        refactored=str(file),
                    )
                    for file in modified_files
                ],
            )

            updated_smells = detect_smells(target_file_copy)
    return refactor_data, updated_smells


def measure_energy_savings(
    original_smell: Smell, refactor_data: RefactoredData | None, updated_smells: list[Smell]
):
    if not refactor_data:
        return None, []

    original_targetFile = original_smell.path
    refactored_targetFile = refactor_data.targetFile.refactored

    # Measure initial energy
    energy_meter = CodeCarbonEnergyMeter()
    energy_meter.measure_energy(Path(original_targetFile))
    initial_emissions = energy_meter.emissions

    if not initial_emissions:
        logging.error("Could not retrieve initial emissions.")
        raise RuntimeError("Could not retrieve initial emissions.")

    logging.info(f"Initial emissions: {initial_emissions}")

    energy_meter.measure_energy(Path(refactored_targetFile))
    final_emissions = energy_meter.emissions

    if not final_emissions:
        logging.error("Could not retrieve final emissions. Discarding refactoring.")
        print("Refactoring Failed.\n")
        return None, []

    elif final_emissions >= initial_emissions:
        logging.info("No measured energy savings. Discarding refactoring.\n")
        print("Refactoring Failed.\n")
        return None, []
    else:
        logging.info("Energy saved!")
        logging.info(f"Initial emissions: {initial_emissions} | Final emissions: {final_emissions}")

        if not TestRunner("pytest", Path(refactor_data.tempDir)).retained_functionality():
            logging.info("Functionality not maintained. Discarding refactoring.\n")
            print("Refactoring Failed.\n")
            return None, []
        else:
            logging.info("Functionality maintained! Retaining refactored file.\n")
            print("Refactoring Succesful!\n")

            refactor_data.energySaved = (
                None
                if math.isnan(final_emissions - initial_emissions)
                else (final_emissions - initial_emissions)
            )

    return refactor_data, updated_smells


def refactor_each_smell_for_type(source_dir: Path, smell: Smell):
    targetFile = smell.path

    logging.info(
        f"Starting refactoring for smell messageId: {smell.messageId} at line {smell.occurences[0].line} in file: {targetFile}"
    )

    if not source_dir.is_dir():
        logging.error(f"Directory {source_dir} does not exist.")

        raise OSError(f"Directory {source_dir} does not exist.")

    refactor_data = None
    updated_smells = []

    tempDir = Path(mkdtemp(prefix="ecooptimizer-"))

    source_copy = tempDir / source_dir.name
    target_file_copy = Path(targetFile.replace(str(source_dir), str(source_copy), 1))

    shutil.copytree(source_dir, source_copy)

    try:
        logging.info(
            f"Running refactorer for smell messageId: {smell.messageId} at line {smell.occurences[0].line} in file: {targetFile}"
        )
        modified_files: list[Path] = refactorer_controller.run_refactorer(
            target_file_copy, source_copy, smell
        )
        logging.info(
            f"Refactorer finished for smell messageId: {smell.messageId} at line {smell.occurences[0].line} in file: {targetFile}"
        )
    except NotImplementedError as e:
        raise RuntimeError(str(e)) from e

    if not TestRunner("pytest", Path(tempDir)).retained_functionality():
        logging.info("Functionality not maintained. Discarding refactoring.\n")
        print("Refactoring Failed.\n")

    else:
        logging.info("Functionality maintained! Retaining refactored file.\n")
        print("Refactoring Succesful!\n")

        refactor_data = RefactoredData(
            tempDir=str(tempDir),
            targetFile=ChangedFile(original=smell.path, refactored=str(target_file_copy)),
            energySaved=None,
            affectedFiles=[
                ChangedFile(
                    original=str(file).replace(str(source_copy), str(source_dir)),
                    refactored=str(file),
                )
                for file in modified_files
            ],
        )

        updated_smells = detect_smells(target_file_copy)
    return refactor_data, updated_smells


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
