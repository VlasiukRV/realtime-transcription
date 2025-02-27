# main.py
import uvicorn

from app.realtime_translation_app import RealTimeTranslation
from app.config import UVICORN_HOST
from app.config import UVICORN_PORT

# Create an instance of the RealTimeTranslation class
real_time_translation_instance = RealTimeTranslation()

# Get the FastAPI app instance from the RealTimeTranslation class
app = real_time_translation_instance.app

if __name__ == '__main__':
    uvicorn.run('main:app', host = UVICORN_HOST, port = UVICORN_PORT)