from dotenv import load_dotenv
import os

from app.services.translators.translator import TranslatorType

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")

WORK_DIR = os.getenv("WORK_DIR")
UVICORN_HOST = os.getenv("UVICORN_HOST")
UVICORN_PORT = int(os.getenv("UVICORN_PORT"))

TRANSLATOR_TYPE = TranslatorType.OPENAI