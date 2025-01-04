# real_time_translation.py

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

from app.webSocketManager import WebSocketManager
from app.transcriber import Transcriber
from app.translator import Translator
from app.utils import logger


class LangRequest(BaseModel):
    lang: str


class RealTimeTranslation:
    def __init__(self):
        """
        Initializes the FastAPI application and all necessary components:
        - WebSocket Manager
        - Transcriber
        - Translator
        """
        # Initialize the FastAPI app
        self.app = FastAPI()

        # Mount static files for serving assets (like JS, CSS, images)
        self.app.mount("/static", StaticFiles(directory="app/static"), name="static")

        self.lang_manager_arr = {}
        # Initialize WebSocket manager for handling WebSocket connections
        self.ws_manager = WebSocketManager()

        # Initialize Jinja2 templates for rendering HTML pages
        self.templates = Jinja2Templates(directory="app/templates")

        # Get the server's hostname for logging purposes
        self.hostname = socket.gethostname()
        logger.info(f"Server hostname: {self.hostname}")

        self.broadcast_task = None
        self.translator = None
        self.transcriber = None
        # Setup FastAPI routes
        self._setup_routes()

    def _setup_routes(self):
        """
        Set up the routes for FastAPI:
        - `/`: Main page
        - `/settings`: Admin settings page
        - `/api/active_clients`: API to get the number of active clients
        - `/api/start`: API to start the worker tasks
        - `/api/stop`: API to stop the worker tasks
        - `/ws/transcribe`: WebSocket endpoint for transcription and translation
        """
        self.app.add_api_route("/", self.get_index, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/settings", self.get_admin, methods=["GET"], response_class=HTMLResponse)

        self.app.add_api_route("/api/addLang", self.add_lang_web_socket, methods=["POST"])
        self.app.add_api_route("/api/start", self.start_worker, methods=["POST"])
        self.app.add_api_route("/api/stop", self.stop_worker, methods=["POST"])
        self.app.add_api_route("/api/state_json", self.get_state_json, methods=["GET"], response_class=JSONResponse)
        # self.app.add_api_route("/api/status", lambda: EventSourceResponse(self.generate_state()), methods=["GET"])
        self.app.add_websocket_route("/ws/transcribe/{lang}", self.websocket_endpoint_handler)

    async def get_index(self, request: Request):
        """
        Returns the main page (index.html).
        If the template is not found, returns a 404 response.
        """
        try:
            return self.templates.TemplateResponse("index.html", {"request": request})
        except FileNotFoundError:
            return HTMLResponse(content="index.html not found", status_code=404)

    async def get_admin(self, request: Request):
        """
        Returns the admin settings page (settings.html).
        It also passes the list of active WebSocket clients to the template.
        """
        try:
            return self.templates.TemplateResponse("settings.html", {
                "request": request
            })
        except FileNotFoundError:
            return HTMLResponse(content="settings.html not found", status_code=404)

    async def get_state_json(self):
        transcriber_status = ""
        if self.transcriber is not None:
            transcriber_status = self.transcriber.get_service_status()

        state_json = {"transcriber_status": transcriber_status, "clients": len(self.ws_manager.active_clients)}
        return state_json

    async def generate_state(self):
        while True:
            state = await self.get_state_json()
            yield f"data: {json.dumps(state)}"
            await asyncio.sleep(5)

    async def add_lang_web_socket(self, lang_request: LangRequest):
        logger.info(lang_request)
        lang = lang_request.lang
        if lang not in self.lang_manager_arr:
            self.lang_manager_arr[lang] = {
                "lang": lang,
                "ws_manager": WebSocketManager(),
                "broadcast_task": None
            }
            await asyncio.sleep(1)
            self.lang_manager_arr[lang]["broadcast_task"] = asyncio.create_task(
                self.lang_manager_arr[lang]["ws_manager"].broadcast_messages())

        return JSONResponse(content={"status": "success", "message": f"Language {lang} added."})

    async def start_worker(self):
        """
        Starts the transcription worker and WebSocket broadcasting tasks.
        This function is triggered via an API endpoint.
        """
        logger.info("Received command to start working task")
        await self.start_working_tasks()
        return "Worker started!"

    async def stop_worker(self):
        """
        Stops the transcription worker and WebSocket broadcasting tasks.
        This function is triggered via an API endpoint.
        """
        logger.info("Received command to stop working task")
        await self.stop_working_tasks()
        return "Worker stopped!"

    async def websocket_endpoint_handler(self, websocket: WebSocket):
        """
        Handles WebSocket connections for transcription and translation.
        This function is triggered when a client connects to the `/ws/transcribe/{lang}` WebSocket endpoint.
        @param websocket:
        @param lang: Language code passed in the URL (e.g., 'en', 'ru')
        """
        lang = websocket.scope["path"].split("/")[3]

        if lang not in self.lang_manager_arr:
            await websocket.close(code=1003)  # Close the connection if the language doesn't exist
            return
        await self.lang_manager_arr[lang]["ws_manager"].handle_connection(websocket)

    def _init_app_services(self):

        self.translator = Translator()
        # Initialize the Transcriber with a sample rate and transcription handler
        self.transcriber = Transcriber(
            sample_rate=16000,
            _handle_transcription=self.handle_transcription
        )

        # Start the transcription thread
        self.transcriber.run()
        # Start the WebSocket message broadcasting task
        for lang in self.lang_manager_arr:
            self.lang_manager_arr[lang]["broadcast_task"] = asyncio.create_task(
                self.lang_manager_arr[lang]["ws_manager"].broadcast_messages())

        # await asyncio.gather(consumer_task)

    async def start_working_tasks(self):
        """
        Starts the transcription and broadcasting tasks.
        The transcription is handled in a separate thread, and messages are broadcast to connected WebSocket clients.
        """

        self._init_app_services()

    async def stop_working_tasks(self):
        """
        Stops the transcription and broadcasting tasks.
        This will clean up resources and stop any active background tasks.
        """

        logger.info("Stopping tasks:")
        for lang in self.lang_manager_arr:
            self.lang_manager_arr[lang]["ws_manager"].stop_message_broadcasting()

        if self.broadcast_task is not None:
            self.broadcast_task.cancel()

        if self.transcriber is not None:
            self.transcriber.close()

    async def handle_transcription(self, transcription_text: str):
        """
        Handles the transcription process, translating the text to the target language
        and sending it to the WebSocket manager for broadcasting.
        """
        for lang in self.lang_manager_arr:
            # Translate the transcribed text
            translated_text = await self.translator.translate_text(
                text=transcription_text,
                target_language=lang
            )
            # Place the translated text in the WebSocket message queue
            await self.lang_manager_arr[lang]["ws_manager"].enqueue_message(translated_text)
