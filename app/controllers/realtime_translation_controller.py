from fastapi import FastAPI, WebSocket
from app.services.realtime_translation import RealTimeTranslation
from app.utils import logger
import socket
from typing import Dict

class RealTimeTranslationController:
    def __init__(self, real_time_translation: RealTimeTranslation):
        self.real_time_translation = real_time_translation
        self.hostname = socket.gethostname()
        logger.info(f"Server hostname: {self.hostname}")

    def setup_routes(self, app: FastAPI) -> None:
        app.add_websocket_route("/ws/transcribe/{lang}", self.handle_language_websocket)

    # WebSocket for language-specific transcription
    async def handle_language_websocket(self, websocket: WebSocket) -> None:

        lang = ""
        try:
            lang = websocket.scope["path"].split("/")[3]
            if lang not in self.real_time_translation.lang_managers:
                logger.warning(f"Language '{lang}' not found. Closing WebSocket.")
                await websocket.close(code=1003)
                return
            await self.real_time_translation.lang_managers[lang].ws_manager.handle_connection(websocket)
        except Exception as e:
            logger.error(f"Error handling websocket for language {lang}: {e}")
            await websocket.close(code=1011)  # Code for internal server error