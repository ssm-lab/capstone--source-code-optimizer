from pydantic import BaseModel
from ecooptimizer.data_types.smell import Smell


class LogInit(BaseModel):
    """Request model for initializing logging.

    Attributes:
        log_dir: Directory path where logs should be stored
    """

    log_dir: str


class SmellRequest(BaseModel):
    """Request model for smell detection endpoint.

    Attributes:
        project_root: Path to the root of the python prohect
        file_path: Path to the Python file to analyze
        enabled_smells: Dictionary mapping smell names to their configurations
    """

    project_root: str
    file_path: str
    enabled_smells: dict[str, dict[str, int | str]]


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
    energySaved: float | None = None
    affectedFiles: list[ChangedFile]


class RefactorRqModel(BaseModel):
    """Request model for single smell refactoring.

    Attributes:
        sourceDir: Directory containing code to refactor
        smell: Smell to refactor
    """

    sourceDir: str
    targetFile: str | None = None
    smell: Smell | None = None
    smellType: str | None = None


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
