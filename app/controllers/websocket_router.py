from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from app.services.realtime_translation import RealTimeTranslation, LangRequest

from app.utils import logger
import socket


class WebsocketRouter:
    def __init__(self, real_time_translation: RealTimeTranslation):
        self.real_time_translation = real_time_translation
        self.templates = Jinja2Templates(directory="app/templates")
        self.hostname = socket.gethostname()
        logger.info(f"Server hostname: {self.hostname}")

    def setup_routes(self, app: FastAPI) -> None:
        app.add_websocket_route("/ws/api", self.handle_api_websocket)

    async def handle_api_websocket(self, websocket: WebSocket) -> None:
        await websocket.accept()

        try:
            while True:
                data = await websocket.receive_text()

                if data == "start":
                    logger.info(f"Starting transcription task")
                    await self.real_time_translation.start_working_tasks()
                    await websocket.send_text("Worker started!")
                elif data == "stop":
                    logger.info(f"Stopping transcription task")
                    await self.real_time_translation.stop_working_tasks()
                    await websocket.send_text("Worker stopped!")
                elif data == "state":
                    # Send system state
                    state = await self.get_system_state()
                    await websocket.send_text(f"State: {state}")
                elif data.startswith("addLang:"):
                    # Add a new language
                    lang_to_add = data.split(":")[1]
                    await self.add_language_to_system(lang_to_add, websocket)
                else:
                    await websocket.send_text("Invalid command")

        except WebSocketDisconnect:
            logger.info(f"Settings-client disconnected")

    # API for adding new languages
    async def add_language(self, lang_request: LangRequest) -> JSONResponse:
        lang = lang_request.lang
        if await self.real_time_translation.add_language(lang):
            return JSONResponse(content={"status": "success", "message": f"Language {lang} added."})
        else:
            return JSONResponse(content={"status": "error", "message": f"Error added Language {lang}"})

