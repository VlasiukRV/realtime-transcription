from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.realtime_translation import RealTimeTranslation, LangRequest
from app.language_manager import LanguageManager
from app.utils import generate_version, logger
import socket
import os
from typing import Dict


class RealTimeTranslationController:
    def __init__(self, real_time_translation: RealTimeTranslation):
        self.real_time_translation = real_time_translation
        self.templates = Jinja2Templates(directory="app/templates")
        self.hostname = socket.gethostname()
        logger.info(f"Server hostname: {self.hostname}")

    def setup_routes(self, app: FastAPI) -> None:
        app.add_api_route("/", self.render_index_page, methods=["GET"], response_class=HTMLResponse)
        app.add_api_route("/settings", self.render_admin_page, methods=["GET"], response_class=HTMLResponse)

        app.add_api_route("/api/addLang", self.add_language, methods=["POST"])
        app.add_api_route("/api/start", self.start_transcription_worker, methods=["POST"])
        app.add_api_route("/api/stop", self.stop_transcription_worker, methods=["POST"])
        app.add_api_route("/api/state_json", self.get_system_state, methods=["GET"], response_class=JSONResponse)

        # app.add_websocket_route("/ws/api", self.handle_api_websocket)
        app.add_websocket_route("/ws/transcribe/{lang}", self.handle_language_websocket)

    # Routes for serving HTML pages
    async def render_index_page(self, request: Request) -> HTMLResponse:
        try:
            versions = self.get_static_file_versions()
            return self.templates.TemplateResponse("index.html", {
                "request": request,
                **versions
            })
        except FileNotFoundError:
            logger.error("index.html not found")
            return HTMLResponse(content="index.html not found", status_code=404)

    async def render_admin_page(self, request: Request) -> HTMLResponse:
        try:
            return self.templates.TemplateResponse("settings.html", {"request": request})
        except FileNotFoundError:
            logger.error("settings.html not found")
            return HTMLResponse(content="settings.html not found", status_code=404)

    # API Endpoints for system state and worker management
    async def get_system_state(self) -> Dict[str, str]:
        transcriber_status = self.real_time_translation.transcriber.get_status() if self.real_time_translation.transcriber else "Not Running"
        return {"transcriber_status": transcriber_status}

    async def start_transcription_worker(self) -> JSONResponse:
        logger.info("Received command to start transcription task")
        await self.real_time_translation.start_working_tasks()
        return JSONResponse(content={"status": "success", "message": "Worker started!"})

    async def stop_transcription_worker(self) -> JSONResponse:
        logger.info("Received command to stop transcription task")
        await self.real_time_translation.stop_working_tasks()
        return JSONResponse(content={"status": "success", "message": "Worker stopped!"})

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

    # API for adding new languages
    async def add_language(self, lang_request: LangRequest) -> JSONResponse:
        lang = lang_request.lang
        if lang not in self.real_time_translation.lang_managers:
            self.real_time_translation.lang_managers[lang] = LanguageManager(lang, self.start_broadcast_for_language)
            logger.info(f"Language {lang} added successfully.")
            return JSONResponse(content={"status": "success", "message": f"Language {lang} added."})
        logger.warning(f"Language {lang} already exists.")
        return JSONResponse(content={"status": "error", "message": f"Language {lang} already exists."})

    # Helper function for broadcasting messages for a specific language
    async def start_broadcast_for_language(self, lang: str) -> None:
        await self.real_time_translation.lang_managers[lang].ws_manager.broadcast_messages()

    def get_static_file_versions(self) -> Dict[str, str]:
        js_file_version = generate_version(os.path.join('/app/static/js/', 'main.js'))
        css_file_version = generate_version(os.path.join('/app/static/css/', 'styles.css'))
        return {"js_file_version": js_file_version, "css_file_version": css_file_version}
