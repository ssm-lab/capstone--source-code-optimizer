# pyright: reportOptionalMemberAccess=false

import asyncio
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException
from pydantic import BaseModel

from ...utils.output_manager import LoggingManager
from ...config import CONFIG

router = APIRouter()


class LogInit(BaseModel):
    log_dir: str


@router.post("/logs/init")
def initialize_logs(log_init: LogInit):
    try:
        loggingManager = LoggingManager(Path(log_init.log_dir), CONFIG["mode"] == "production")
        CONFIG["loggingManager"] = loggingManager
        CONFIG["detectLogger"] = loggingManager.loggers["detect"]
        CONFIG["refactorLogger"] = loggingManager.loggers["refactor"]

        return {"message": "Logging initialized succesfully."}
    except Exception as e:
        raise WebSocketException(code=500, reason=str(e)) from e


@router.websocket("/logs/main")
async def websocket_main_logs(websocket: WebSocket):
    await websocket_log_stream(websocket, CONFIG["loggingManager"].log_files["main"])


@router.websocket("/logs/detect")
async def websocket_detect_logs(websocket: WebSocket):
    await websocket_log_stream(websocket, CONFIG["loggingManager"].log_files["detect"])


@router.websocket("/logs/refactor")
async def websocket_refactor_logs(websocket: WebSocket):
    await websocket_log_stream(websocket, CONFIG["loggingManager"].log_files["refactor"])


async def websocket_log_stream(websocket: WebSocket, log_file: Path):
    """Streams log file content via WebSocket."""
    await websocket.accept()
    try:
        with log_file.open(encoding="utf-8") as file:
            file.seek(0, 2)  # Start at file end
            while True:
                line = file.readline()
                if line:
                    await websocket.send_text(line)
                else:
                    await asyncio.sleep(0.5)
    except FileNotFoundError:
        await websocket.send_text("Error: Log file not found.")
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        await websocket.close()
