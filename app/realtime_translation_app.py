import asyncio
import socket
import json

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.web_socket_manager import WebSocketManager
from app.transcriber import Transcriber
from app.translator import Translator
from app.utils import logger


class LangRequest(BaseModel):
    lang: str


class RealTimeTranslation:
    def __init__(self):
        self.app = FastAPI()

        # Mount static files
        self.app.mount("/static", StaticFiles(directory="app/static"), name="static")

        # Initialize components
        self.lang_manager_arr = {}
        self.ws_manager = WebSocketManager()
        self.templates = Jinja2Templates(directory="app/templates")
        self.hostname = socket.gethostname()

        # Log hostname
        logger.info(f"Server hostname: {self.hostname}")

        # Initialize services
        self.translator = Translator()
        self.transcriber = Transcriber(sample_rate=16000, _handle_transcription=self.handle_transcription)

        # Define routes
        self._setup_routes()

    def _setup_routes(self):
        """
        Define FastAPI routes.
        """
        self.app.add_api_route("/", self.get_index, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/settings", self.get_admin, methods=["GET"], response_class=HTMLResponse)

        self.app.add_api_route("/api/addLang", self.add_lang_web_socket, methods=["POST"])
        self.app.add_api_route("/api/start", self.start_worker, methods=["POST"])
        self.app.add_api_route("/api/stop", self.stop_worker, methods=["POST"])
        self.app.add_api_route("/api/state_json", self.get_state_json, methods=["GET"], response_class=JSONResponse)
        self.app.add_websocket_route("/ws/transcribe/{lang}", self.websocket_endpoint_handler)

    async def get_index(self, request: Request):
        try:
            return self.templates.TemplateResponse("index.html", {"request": request})
        except FileNotFoundError:
            return HTMLResponse(content="index.html not found", status_code=404)

    async def get_admin(self, request: Request):
        try:
            return self.templates.TemplateResponse("settings.html", {"request": request})
        except FileNotFoundError:
            return HTMLResponse(content="settings.html not found", status_code=404)

    async def get_state_json(self):
        transcriber_status = self.transcriber.get_service_status() if self.transcriber else "Not Running"
        state_json = {
            "transcriber_status": transcriber_status,
            "clients": len(self.ws_manager.active_clients)
        }
        return state_json

    async def add_lang_web_socket(self, lang_request: LangRequest):
        lang = lang_request.lang
        if lang not in self.lang_manager_arr:
            self.lang_manager_arr[lang] = {
                "lang": lang,
                "ws_manager": WebSocketManager(),
                "broadcast_task": asyncio.create_task(self.create_broadcast_task(lang))
            }
            return JSONResponse(content={"status": "success", "message": f"Language {lang} added."})
        return JSONResponse(content={"status": "error", "message": f"Language {lang} already exists."})

    async def create_broadcast_task(self, lang: str):
        """
        Helper function to start broadcasting messages for a specific language.
        """
        await self.lang_manager_arr[lang]["ws_manager"].broadcast_messages()

    async def start_worker(self):
        logger.info("Received command to start working task")
        await self.start_working_tasks()
        return "Worker started!"

    async def stop_worker(self):
        logger.info("Received command to stop working task")
        await self.stop_working_tasks()
        return "Worker stopped!"

    async def websocket_endpoint_handler(self, websocket: WebSocket):
        lang = websocket.scope["path"].split("/")[3]

        if lang not in self.lang_manager_arr:
            await websocket.close(code=1003)
            return
        await self.lang_manager_arr[lang]["ws_manager"].handle_connection(websocket)

    async def start_working_tasks(self):
        logger.info("Starting transcription and broadcasting tasks...")
        self.transcriber.run()
        for lang in self.lang_manager_arr:
            self.lang_manager_arr[lang]["broadcast_task"] = asyncio.create_task(
                self.create_broadcast_task(lang)
            )

    async def stop_working_tasks(self):
        logger.info("Stopping tasks...")
        for lang in self.lang_manager_arr:
            self.lang_manager_arr[lang]["ws_manager"].stop_message_broadcasting()
        if self.transcriber:
            self.transcriber.close()

    async def handle_transcription(self, transcription_text: str):
        """
        Handle transcription and translation for each language.
        """
        tasks = []
        for lang in self.lang_manager_arr:
            tasks.append(self.translate_and_broadcast(lang, transcription_text))
        await asyncio.gather(*tasks)

    async def translate_and_broadcast(self, lang: str, transcription_text: str):
        translated_text = await self.translator.translate_text(
            text=transcription_text,
            target_language=lang
        )
        await self.lang_manager_arr[lang]["ws_manager"].enqueue_message(translated_text)
