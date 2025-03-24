from dotenv import load_dotenv
import os

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")

WORK_DIR = os.getenv("WORK_DIR")
UVICORN_HOST = os.getenv("UVICORN_HOST")
UVICORN_PORT = int(os.getenv("UVICORN_PORT"))