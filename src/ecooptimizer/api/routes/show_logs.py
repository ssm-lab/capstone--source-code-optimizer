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


async def listen_for_disconnect(websocket: WebSocket):
    """Listens for client disconnects."""
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


async def websocket_log_stream(websocket: WebSocket, log_file: Path):
    """Streams log file content via WebSocket."""
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
