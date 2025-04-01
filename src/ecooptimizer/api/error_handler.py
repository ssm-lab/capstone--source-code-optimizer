# ecooptimizer/api/error_handler.py
import logging
import os
import stat

from fastapi import Request
from fastapi.responses import JSONResponse

from ecooptimizer.config import CONFIG


class AppError(Exception):
    """Base class for all application errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EnergySavingsError(AppError):
    """Raised when energy savings validation fails."""

    def __init__(self):
        message = "Energy was not saved after refactoring."
        super().__init__(message, 400)


class EnergyMeasurementError(AppError):
    """Raised when energy measurement fails."""

    def __init__(self, file_path: str):
        message = f"Could not retrieve emissions of {file_path}."
        super().__init__(message, 400)


class RefactoringError(AppError):
    """Raised when refactoring fails."""

    pass


class RessourceNotFoundError(AppError):
    """Raised when a ressource (file or folder) cannot be found."""

    def __init__(self, path: str, ressourceType: str):
        message = f"{ressourceType.capitalize()} not found: {path}."
        super().__init__(message, 404)


def get_route_logger(request: Request):
    """Determine which logger to use based on route path."""
    route_path = request.url.path
    if "/detect" in route_path.lower():
        return CONFIG["detectLogger"]
    elif "/refactor" in route_path.lower():
        return CONFIG["refactorLogger"]
    return logging.getLogger()


async def global_error_handler(request: Request, e: Exception) -> JSONResponse:
    logger = get_route_logger(request)

    if isinstance(e, AppError):
        logger.error(f"Application error at {request.url.path}: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.message},
        )
    else:
        logger.error(f"Unexpected error at {request.url.path}", e)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


def remove_readonly(func, path, _) -> None:  # noqa: ANN001
    """Removes readonly attribute from files/directories to enable deletion.

    Args:
        func: Original removal function that failed
        path: Path to the file/directory
        _: Unused excinfo parameter

    Note:
        Used as error handler for shutil.rmtree()
    """
    os.chmod(path, stat.S_IWRITE)  # noqa: PTH101
    func(path)
