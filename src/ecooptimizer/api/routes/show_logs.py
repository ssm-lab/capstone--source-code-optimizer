import asyncio
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ecooptimizer import OUTPUT_MANAGER

router = APIRouter()


@router.websocket("/logs/main")
async def websocket_main_logs(websocket: WebSocket):
    """Handles WebSocket connections for real-time log streaming."""
    await stream_log_file(websocket, OUTPUT_MANAGER.log_files["main"])


async def stream_log_file(websocket: WebSocket, log_file: Path):
    """Streams log file content to a WebSocket connection."""
    await websocket.accept()
    try:
        with Path(log_file).open(encoding="utf-8") as file:
            file.seek(0, 2)  # Move to the end of the file.
            while True:
                line = file.readline()
                if line:
                    await websocket.send_text(line.strip())
                else:
                    await asyncio.sleep(0.5)
    except FileNotFoundError:
        await websocket.send_text("Error: Log file not found.")
        await websocket.close()
    except WebSocketDisconnect:
        print("WebSocket disconnected")
