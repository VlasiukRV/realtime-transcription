from fastapi import APIRouter, WebSocket, Depends
from starlette.websockets import WebSocketDisconnect

from app.services.realtime_translation import RealTimeTranslation
from app.api.dependencies import get_real_time_translation
from app.api.http_router import router as http_router
from app.utils import logger

app_router = APIRouter()

@app_router.websocket("/ws/ping")
async def websocket_ping(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_text("pong")
        while True:
            await websocket.receive_text()  # Keep it open if needed
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011)

@app_router.websocket("/ws/transcribe/{lang}")
async def handle_lang_transcription_websocket(
        websocket: WebSocket,
        lang: str,
        real_time_translation: RealTimeTranslation = Depends(get_real_time_translation)
) -> None:
    try:
        if not lang:
            logger.warning("Language not specified in the WebSocket path. Closing WebSocket.")
            await websocket.close(code=1003)
        if not await real_time_translation.handle_websocket_connection(lang, websocket):
            logger.warning(f"Error handling websocket for language {lang}. Closing WebSocket.")
            await websocket.close(code=1003)
    except Exception as e:
        logger.error(f"Error handling websocket for language {lang}: {e}")
        await websocket.close(code=1011)  # Code for internal server error

app_router.include_router(http_router)