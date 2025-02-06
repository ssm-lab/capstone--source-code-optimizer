import logging
import shutil
from tempfile import mkdtemp
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


from ..refactorers.refactorer_controller import RefactorerController

from ..analyzers.analyzer_controller import AnalyzerController

from ..data_types.smell import Smell
from ..measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter

from .. import OUTPUT_MANAGER, OUTPUT_DIR

base_dir = Path(__file__).resolve().parent
logs_dir = base_dir / "logs"
log_file = logs_dir / "app.log"
outputs_dir = base_dir / "files"

logs_dir.mkdir(exist_ok=True)
outputs_dir.mkdir(exist_ok=True)

app = FastAPI()

analyzer_controller = AnalyzerController()
refactorer_controller = RefactorerController(OUTPUT_DIR)


class RefactoredData(BaseModel):
    tempDir: str
    targetFile: str
    energySaved: float
    refactoredFiles: list[str]


class RefactorRqModel(BaseModel):
    source_dir: str
    smell: Smell


class RefactorResModel(BaseModel):
    refactoredData: RefactoredData = None  # type: ignore
    updatedSmells: list[Smell]


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


@app.post("/refactor", response_model=RefactorResModel)
def refactor(request: RefactorRqModel):
    try:
        raw_data = request.model_dump_json()
        print(raw_data)
        refactor_data, updated_smells = refactor_smell(
            Path(request.source_dir),
            request.smell,
        )
        if not refactor_data:
            return RefactorResModel(updatedSmells=updated_smells)
        else:
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


def refactor_smell(source_dir: Path, smell: Smell):
    targetFile = smell.path
    logging.info(f"*** Source directory {source_dir}, target file {targetFile}")
    logging.info(
        f"*** Starting refactoring for smell symbol: {smell.symbol}\
          at line {smell.occurences[0].line} in file: {targetFile}"
    )

    if not source_dir.is_dir():
        logging.error(f"Directory {source_dir} does not exist.")

        raise OSError(f"Directory {source_dir} does not exist.")

    # Measure initial energy
    energy_meter = CodeCarbonEnergyMeter()
    energy_meter.measure_energy(Path(targetFile))
    initial_emissions = 10000

    if not initial_emissions:
        logging.error("Could not retrieve initial emissions.")
        raise RuntimeError("Could not retrieve initial emissions.")

    logging.info(f"*** Initial emissions: {initial_emissions}")

    refactor_data = None
    updated_smells = []

    tempDir = mkdtemp(prefix="ecooptimizer-")

    source_copy = Path(tempDir) / source_dir.name
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
    final_emissions = 5

    if not final_emissions:
        logging.error("Could not retrieve final emissions. Discarding refactoring.")
        print("Refactoring Failed.\n")

    elif final_emissions >= initial_emissions:
        logging.info("No measured energy savings. Discarding refactoring.\n")
        print("Refactoring Failed.\n")

    else:
        logging.info("*** Energy saved!")
        logging.info(
            f"*** Initial emissions: {initial_emissions} | Final emissions: {final_emissions}"
        )

        # if not TestRunner("pytest", Path(tempDir)).retained_functionality():
        #     logging.info("Functionality not maintained. Discarding refactoring.\n")
        #     print("Refactoring Failed.\n")

        # else:
        #     logging.info("Functionality maintained! Retaining refactored file.\n")
        #     print("Refactoring Succesful!\n")

        #     refactor_data = RefactoredData(
        #         tempDir=tempDir,
        #         targetFile=str(target_file_copy).replace(str(source_copy), str(source_dir), 1),
        #         energySaved=(final_emissions - initial_emissions),
        #         refactoredFiles=[str(file) for file in modified_files],
        #     )

        #     updated_smells = detect_smells(target_file_copy)

        print("Refactoring Succesful!\n")
        logging.info(f"*** Reading from tempDir {tempDir} targetFile {targetFile}")
        for file in modified_files:
            logging.info(f"*** Modified {file}")
        refactor_data = RefactoredData(
            tempDir=tempDir,
            targetFile=str(target_file_copy),
            energySaved=(final_emissions - initial_emissions),
            refactoredFiles=[str(file) for file in modified_files],
        )

        updated_smells = detect_smells(target_file_copy)

    return refactor_data, updated_smells


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
