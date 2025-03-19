from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.services.realtime_translation import RealTimeTranslation, LangRequest
from app.utils import generate_version, logger
import socket
import os
from typing import Dict


def get_static_file_versions_for_index_page() -> Dict[str, str]:
    js_file_version = generate_version(os.path.join('/app/static/js/', 'main.js'))
    css_file_version = generate_version(os.path.join('/app/static/css/', 'styles.css'))
    return {"js_file_version": js_file_version, "css_file_version": css_file_version}

def get_static_file_versions_for_admin_page() -> Dict[str, str]:
    js_file_version = generate_version(os.path.join('/app/static/js/', 'settings.js'))
    css_file_version = generate_version(os.path.join('/app/static/css/', 'styles.css'))
    return {"js_file_version": js_file_version, "css_file_version": css_file_version}

class HTTPController:
    def __init__(self, templates: Jinja2Templates, real_time_translation: RealTimeTranslation):
        self.real_time_translation = real_time_translation
        self.templates = templates
        self.hostname = socket.gethostname()
        logger.info(f"Server hostname: {self.hostname}")

    def setup_routes(self, app: FastAPI) -> None:
        app.add_api_route("/", self.render_index_page, methods=["GET"], response_class=HTMLResponse)
        app.add_api_route("/settings", self.render_admin_page, methods=["GET"], response_class=HTMLResponse)

        app.add_api_route("/api/addLang", self.add_language, methods=["POST"])
        app.add_api_route("/api/start", self.start_transcription_worker, methods=["POST"])
        app.add_api_route("/api/stop", self.stop_transcription_worker, methods=["POST"])
        app.add_api_route("/api/state_json", self.get_system_state, methods=["GET"], response_class=JSONResponse)

    # Routes for serving HTML pages
    async def render_index_page(self, request: Request) -> HTMLResponse:
        try:
            versions = get_static_file_versions_for_index_page()
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
    async def get_system_state(self) -> JSONResponse:
        transcriber_status = self.real_time_translation.transcriber.get_status() if self.real_time_translation.transcriber else "Not Running"
        return JSONResponse(content={"transcriber_status": transcriber_status})

    async def start_transcription_worker(self) -> JSONResponse:
        await self.real_time_translation.start_working_tasks()
        return JSONResponse(content={"status": "success", "message": "Worker started!"})

    async def stop_transcription_worker(self) -> JSONResponse:
        await self.real_time_translation.stop_working_tasks()
        return JSONResponse(content={"status": "success", "message": "Worker stopped!"})

    # API for adding new languages
    async def add_language(self, lang_request: LangRequest) -> JSONResponse:
        lang = lang_request.lang
        if await self.real_time_translation.add_language(lang):
            return JSONResponse(content={"status": "success", "message": f"Language {lang} added."})
        else:
            return JSONResponse(content={"status": "error", "message": f"Error added Language {lang}"})
