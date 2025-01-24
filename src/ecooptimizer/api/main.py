# import logging
# from pathlib import Path
# from typing import Dict, List, Optional
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from ..data_wrappers.smell import Smell
# from ..utils.ast_parser import parse_file
# from ..measurements.codecarbon_energy_meter import CodeCarbonEnergyMeter
# from ..analyzers.pylint_analyzer import PylintAnalyzer
# from ..utils.refactorer_factory import RefactorerFactory
# import uvicorn

# outputs_dir = Path("/Users/tanveerbrar/Desktop").resolve()
# app = FastAPI()


# class OccurrenceModel(BaseModel):
#     line: int
#     column: int
#     call_string: str


# class SmellModel(BaseModel):
#     absolutePath: Optional[str] = None
#     column: Optional[int] = None
#     confidence: str
#     endColumn: Optional[int] = None
#     endLine: Optional[int] = None
#     line: Optional[int] = None
#     message: str
#     messageId: str
#     module: Optional[str] = None
#     obj: Optional[str] = None
#     path: Optional[str] = None
#     symbol: str
#     type: str
#     repetitions: Optional[int] = None
#     occurrences: Optional[List[OccurrenceModel]] = None


# class RefactorRqModel(BaseModel):
#     file_path: str
#     smell: SmellModel


# app = FastAPI()


# @app.get("/smells", response_model=List[SmellModel])
# def get_smells(file_path: str):
#     try:
#         smells = detect_smells(Path(file_path))
#         return smells
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="File not found")


# @app.post("/refactor")
# def refactor(request: RefactorRqModel, response_model=Dict[str, object]):
#     try:
#         refactored_code, energy_difference, updated_smells = refactor_smell(
#             Path(request.file_path), request.smell
#         )
#         return {
#             "refactoredCode": refactored_code,
#             "energyDifference": energy_difference,
#             "updatedSmells": updated_smells,
#         }
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# def detect_smells(file_path: Path) -> list[Smell]:
#     """
#     Detect code smells in a given file.

#     Args:
#         file_path (Path): Path to the Python file to analyze.

#     Returns:
#         List[Smell]: A list of detected smells.
#     """
#     logging.info(f"Starting smell detection for file: {file_path}")
#     if not file_path.is_file():
#         logging.error(f"File {file_path} does not exist.")
#         raise FileNotFoundError(f"File {file_path} does not exist.")

#     source_code = parse_file(file_path)
#     analyzer = PylintAnalyzer(file_path, source_code)
#     analyzer.analyze()
#     analyzer.configure_smells()

#     smells_data: list[Smell] = analyzer.smells_data
#     logging.info(f"Detected {len(smells_data)} code smells.")
#     return smells_data


# def refactor_smell(file_path: Path, smell: SmellModel) -> tuple[str, float, List[Smell]]:
#     logging.info(
#         f"Starting refactoring for file: {file_path} and smell symbol: {smell.symbol} at line {smell.line}"
#     )

#     if not file_path.is_file():
#         logging.error(f"File {file_path} does not exist.")
#         raise FileNotFoundError(f"File {file_path} does not exist.")

#     # Measure initial energy
#     energy_meter = CodeCarbonEnergyMeter(file_path)
#     energy_meter.measure_energy()
#     initial_emissions = energy_meter.emissions

#     if not initial_emissions:
#         logging.error("Could not retrieve initial emissions.")
#         raise RuntimeError("Could not retrieve initial emissions.")

#     logging.info(f"Initial emissions: {initial_emissions}")

#     # Refactor the code smell
#     refactorer = RefactorerFactory.build_refactorer_class(smell.messageId, outputs_dir)
#     if not refactorer:
#         logging.error(f"No refactorer implemented for smell {smell.symbol}.")
#         raise NotImplementedError(f"No refactorer implemented for smell {smell.symbol}.")

#     refactorer.refactor(file_path, smell.dict(), initial_emissions)

#     target_line = smell.line
#     updated_path = outputs_dir / f"refactored_source/{file_path.stem}_LPLR_line_{target_line}.py"
#     logging.info(f"Refactoring completed. Updated file: {updated_path}")

#     # Measure final energy
#     energy_meter.measure_energy()
#     final_emissions = energy_meter.emissions

#     if not final_emissions:
#         logging.error("Could not retrieve final emissions.")
#         raise RuntimeError("Could not retrieve final emissions.")

#     logging.info(f"Final emissions: {final_emissions}")

#     energy_difference = initial_emissions - final_emissions
#     logging.info(f"Energy difference: {energy_difference}")

#     # Detect remaining smells
#     updated_smells = detect_smells(updated_path)

#     # Read refactored code
#     with Path.open(updated_path) as file:
#         refactored_code = file.read()

#     return refactored_code, energy_difference, updated_smells


# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)
