# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.realtime_translation import RealTimeTranslation
from app.controllers.realtime_translation_controller import RealTimeTranslationController
from app.controllers.http_controller import HTTPController
from app.controllers.websocket_controller import WebsocketController

from app.config import UVICORN_HOST
from app.config import UVICORN_PORT

def create_app():
    application = FastAPI(title="RealTime-transcription", version="1.0.1")

    # Mount static files
    application.mount("/static", StaticFiles(directory="app"), name="static")

    templates = Jinja2Templates(directory="app/templates")

    # Initialize services
    real_time_translation = RealTimeTranslation()

    # Set up controllers
    realtime_translation_controller = RealTimeTranslationController(real_time_translation)
    realtime_translation_controller.setup_routes(application)

    http_controller = HTTPController(templates, real_time_translation)
    http_controller.setup_routes(application)

    websocket_controller = WebsocketController(real_time_translation)
    websocket_controller.setup_routes(application)

    return application

app = create_app()

if __name__ == '__main__':
    uvicorn.run('main:app', host = UVICORN_HOST, port = UVICORN_PORT)