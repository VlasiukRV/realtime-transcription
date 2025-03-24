from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from api import get_real_time_translation
from app.services.realtime_translation import RealTimeTranslation

from app.utils import logger
import socket

router = APIRouter()

@router.websocket("/ws/api")
async def handle_api_websocket(
        websocket: WebSocket,
        real_time_translation: RealTimeTranslation = Depends(get_real_time_translation)
) -> None:

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            if data == "start":
                logger.info(f"Starting transcription task")
                await real_time_translation.start_working_tasks()
                await websocket.send_text("Worker started!")
            elif data == "stop":
                logger.info(f"Stopping transcription task")
                await real_time_translation.stop_working_tasks()
                await websocket.send_text("Worker stopped!")
            elif data.startswith("addLang:"):
                # Add a new language
                lang_to_add = data.split(":")[1]
                await real_time_translation.add_language(lang_to_add)
            else:
                await websocket.send_text("Invalid command")

    except WebSocketDisconnect:
        logger.info(f"Settings-client disconnected")
