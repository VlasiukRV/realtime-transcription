from fastapi import WebSocket, Depends
import asyncio
from typing import Dict

from app.services.dependencies import get_translator
from app.services.transcribers.transcriber import Transcriber
from app.services.translators.translator import ITranslator
from app.services.language_manager import LanguageManager
from app.utils import logger

class RealTimeTranslation:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 translator: ITranslator = Depends(get_translator)
    ):
        # Initialize services
        if not hasattr(self, 'initialized'):  # Protecting from re-initialization
            self.transcriber = Transcriber(sample_rate=16000, _handle_transcription=self._handle_transcription)

            self.translator = translator

            self.lang_managers: Dict[str, LanguageManager] = {}

            # Mark as initialized
            self.initialized = True

    async def handle_websocket_connection(self, lang: str, websocket: WebSocket) -> bool:
        """
        Handle WebSocket connection for a specific language.
        """
        if lang not in self.lang_managers:
            return False

        await self.lang_managers[lang].ws_manager.handle_connection(websocket)
        return True

    async def add_language(self, lang: str) -> bool:
        """
        Add a new language for translation and processing.
        """
        if lang not in self.lang_managers:
            lang_manager = LanguageManager(lang)
            await lang_manager.start_broadcasting()

            self.lang_managers[lang] = lang_manager
            logger.info(f"Language {lang} added successfully.")
            return True

        logger.warning(f"Language {lang} already exists.")
        return False

    async def start_working_tasks(self):
        """
        Start all transcription and broadcasting tasks for each language.
        """
        logger.info("\033[33mStarting transcription and broadcasting tasks...\033[0m")
        self.transcriber.start()
        for lang in self.lang_managers:
            await self.lang_managers[lang].start_broadcasting()

    async def stop_working_tasks(self):
        """
        Stop all transcription and broadcasting tasks.
        """
        logger.info("\033[33mStopping transcription and broadcasting tasks...\033[0m")
        for lang in list(self.lang_managers.keys()):
            await self.lang_managers[lang].stop()
        self.lang_managers.clear()
        if self.transcriber:
            self.transcriber.stop()

    async def _handle_transcription(self, transcription_text: str):
        """
        Handle transcription and translation for each language.
        """
        tasks = []
        for lang in self.lang_managers:
            tasks.append(self._translate_and_broadcast(lang, transcription_text))
        await asyncio.gather(*tasks)

    async def _translate_and_broadcast(self, lang: str, transcription_text: str):
        """
        Translate text and send it through WebSocket.
        """
        translated_text = await self.translator.translate_text(
            text=transcription_text,
            target_language=lang
        )
        await self.lang_managers[lang].ws_manager.enqueue_message(translated_text)
