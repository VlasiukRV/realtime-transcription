# main.py
from app.realtime_translation_app import RealTimeTranslation

# Create an instance of the RealTimeTranslation class
real_time_translation_instance = RealTimeTranslation()

# Get the FastAPI app instance from the RealTimeTranslation class
app = real_time_translation_instance.app
