from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.templating import Jinja2Templates

from app.services.realtime_translation import RealTimeTranslation
from app.api.dependencies import get_real_time_translation, get_jinja_template, get_static_file_versions_for_index_page, \
    get_static_file_versions_for_admin_page
from app.utils import logger


from pydantic import BaseModel


class LangRequest(BaseModel):
    lang: str

router = APIRouter()

@router.get("/")
async def render_index_page(
        request: Request,
        templates: Jinja2Templates = Depends(get_jinja_template)
) -> HTMLResponse:
    try:
        versions = get_static_file_versions_for_index_page()
        return templates.TemplateResponse("index.html", {
            "request": request,
            **versions
        })
    except FileNotFoundError:
        logger.error("index.html not found")
        return HTMLResponse(content="index.html not found", status_code=404)


@router.get("/settings")
async def render_settings_page(
        request: Request,
        templates: Jinja2Templates = Depends(get_jinja_template)
) -> HTMLResponse:
    try:
        versions = get_static_file_versions_for_admin_page()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            **versions
        })
    except FileNotFoundError:
        logger.error("settings.html not found")
        return HTMLResponse(content="settings.html not found", status_code=404)

@router.post("/api/addLang")
async def add_language(
    lang_request: LangRequest,
    real_time_translation: RealTimeTranslation = Depends(get_real_time_translation)
) -> JSONResponse:
    lang = lang_request.lang
    if await real_time_translation.add_language(lang):
        data = {"transcriber_status": "success", "message": f"Language {lang} added."}
    else:
        data = {"transcriber_status": "error", "message": f"Error adding Language {lang}"}

    return JSONResponse(content=data, status_code=200)

@router.post("/api/start")
async def start_transcription_worker(
    real_time_translation: RealTimeTranslation = Depends(get_real_time_translation)
) -> JSONResponse:
    await real_time_translation.start_working_tasks()
    data = {"transcriber_status": "success", "message": f"Worker started!"}
    return JSONResponse(content=data, status_code=200)

@router.post("/api/stop")
async def stop_transcription_worker(
    real_time_translation: RealTimeTranslation = Depends(get_real_time_translation)
) -> JSONResponse:
    await real_time_translation.stop_working_tasks()
    data = {"transcriber_status": "success", "message": f"Worker stopped!"}
    return JSONResponse(content=data, status_code=200)

@router.get("/api/stop")
# API Endpoints for system state and worker management
async def get_system_state(
    real_time_translation: RealTimeTranslation = Depends(get_real_time_translation)
) -> JSONResponse:
    transcriber_status = real_time_translation.transcriber.get_status() if real_time_translation.transcriber else {
        "status": "error", "message": "Not Running"}
    return JSONResponse(
        content={"transcriber_status": transcriber_status["status"], "message": transcriber_status["message"]})

