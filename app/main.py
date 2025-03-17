# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.realtime_translation import RealTimeTranslation
from app.realtime_translation_controller import RealTimeTranslationController
from app.config import UVICORN_HOST
from app.config import UVICORN_PORT

def create_app():
    application = FastAPI(title="RealTime-transcription", version="1.0.1")
    # Mount static files
    application.mount("/static", StaticFiles(directory="app/static"), name="static")

    # Initialize services
    real_time_translation = RealTimeTranslation()

    # Set up controllers
    controller = RealTimeTranslationController(real_time_translation)
    controller.setup_routes(application)

    return application

app = create_app()

if __name__ == '__main__':
    uvicorn.run('main:app', host = UVICORN_HOST, port = UVICORN_PORT)