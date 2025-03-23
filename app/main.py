# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.realtime_translation import RealTimeTranslation
from app.services.translators.translator import TranslatorType
from app.controllers.realtime_translation_router import RealTimeTranslationRouter
from app.controllers.http_router import HTTPRouter
from app.controllers.websocket_router import WebsocketRouter

from app.config import UVICORN_HOST
from app.config import UVICORN_PORT

def create_app():
    application = FastAPI(title="RealTime-transcription", version="1.0.1")

    # Mount static files
    application.mount("/static", StaticFiles(directory="app/static"), name="static")

    templates = Jinja2Templates(directory="app/templates")

    # Initialize services
    real_time_translation = RealTimeTranslation(TranslatorType.GOOGLE)

    # Set up controllers
    http_router = HTTPRouter(templates, real_time_translation)
    http_router.setup_routes(application)

    realtime_translation_router = RealTimeTranslationRouter(real_time_translation)
    realtime_translation_router.setup_routes(application)

    # websocket_controller = WebsocketController(real_time_translation)
    # websocket_controller.setup_routes(application)

    return application

app = create_app()

if __name__ == '__main__':
    uvicorn.run('main:app', host = UVICORN_HOST, port = UVICORN_PORT)