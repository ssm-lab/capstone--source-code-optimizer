"""WebSocket endpoints for real-time log streaming."""

# pyright: reportOptionalMemberAccess=false
import asyncio
from pathlib import Path
import re
from fastapi import APIRouter, WebSocketException
from fastapi.websockets import WebSocketState, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ...utils.output_manager import LoggingManager
from ...config import CONFIG

router = APIRouter()


class LogInit(BaseModel):
    """Request model for initializing logging.

    Attributes:
        log_dir: Directory path where logs should be stored
    """

    log_dir: str


@router.post("/logs/init", summary="Initialize logging system")
def initialize_logs(log_init: LogInit) -> dict[str, str]:
    """Initializes the logging manager and configures application loggers.

    Args:
        log_init: Contains the log directory path

    Returns:
        dict: Success message

    Raises:
        WebSocketException: If initialization fails
    """
    try:
        loggingManager = LoggingManager(Path(log_init.log_dir), CONFIG["mode"] == "production")
        CONFIG["loggingManager"] = loggingManager
        CONFIG["detectLogger"] = loggingManager.loggers["detect"]
        CONFIG["refactorLogger"] = loggingManager.loggers["refactor"]

        return {"message": "Logging initialized successfully."}
    except Exception as e:
        raise WebSocketException(code=500, reason=str(e)) from e


@router.websocket("/logs/main")
async def websocket_main_logs(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming main application logs."""
    await websocket_log_stream(websocket, CONFIG["loggingManager"].log_files["main"])


@router.websocket("/logs/detect")
async def websocket_detect_logs(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming code detection logs."""
    await websocket_log_stream(websocket, CONFIG["loggingManager"].log_files["detect"])


@router.websocket("/logs/refactor")
async def websocket_refactor_logs(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming code refactoring logs."""
    await websocket_log_stream(websocket, CONFIG["loggingManager"].log_files["refactor"])


async def listen_for_disconnect(websocket: WebSocket) -> None:
    """Background task to monitor WebSocket connection state.

    Args:
        websocket: The WebSocket connection to monitor

    Raises:
        WebSocketDisconnect: When client disconnects
    """
    try:
        while True:
            await websocket.receive()

            if websocket.client_state == WebSocketState.DISCONNECTED:
                raise WebSocketDisconnect()
    except WebSocketDisconnect:
        print("WebSocket disconnected from client.")
        raise
    except Exception as e:
        print(f"Unexpected error in listener: {e}")


async def websocket_log_stream(websocket: WebSocket, log_file: Path) -> None:
    """Streams log file content to WebSocket client in real-time.

    Args:
        websocket: Active WebSocket connection
        log_file: Path to the log file to stream

    Note:
        Only streams INFO, WARNING, ERROR, and CRITICAL level messages
        Automatically handles client disconnects
    """
    await websocket.accept()

    # Start background task to listen for disconnect
    listener_task = asyncio.create_task(listen_for_disconnect(websocket))

    try:
        with log_file.open(encoding="utf-8") as file:
            file.seek(0, 2)  # Seek to end of the file
            while not listener_task.done():
                if websocket.application_state != WebSocketState.CONNECTED:
                    raise WebSocketDisconnect(reason="Connection closed")
                line = file.readline()
                if line:
                    match = re.search(r"\[\b(ERROR|DEBUG|INFO|WARNING|TRACE)\b]", line)
                    if match:
                        level = match.group(1)

                        if level in ("INFO", "WARNING", "ERROR", "CRITICAL"):
                            await websocket.send_text(line)
                else:
                    await asyncio.sleep(0.1)  # Short sleep when no new lines
    except FileNotFoundError:
        await websocket.send_text("Error: Log file not found.")
    except WebSocketDisconnect as e:
        print(e.reason)
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        listener_task.cancel()
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
