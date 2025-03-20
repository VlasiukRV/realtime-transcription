from fastapi import WebSocket

from app.services.transcriber import  Transcriber
from app.services.translators.translator import TranslatorFactory, TranslatorType
from app.services.language_manager import LanguageManager
from app.utils import logger

from pydantic import BaseModel

import asyncio


class LangRequest(BaseModel):
    lang: str


class RealTimeTranslation:
    def __init__(self, translator_type: TranslatorType):

        # Initialize services
        self.transcriber = Transcriber(sample_rate=16000, _handle_transcription=self._handle_transcription)

        translator_factory = TranslatorFactory()
        translator_class = translator_factory.get_translator(translator_type)
        self.translator = translator_class()

        self.lang_managers: dict[str, LanguageManager] = {}

    async def handle_websocket_connection(self, lang: str, websocket: WebSocket) -> bool:
        if lang not in self.lang_managers:
            return False

        await self.lang_managers[lang].ws_manager.handle_connection(websocket)

        return True

    async def add_language(self, lang: str) -> bool:

        if lang not in self.lang_managers:
            lang_manager = LanguageManager(lang)
            await lang_manager.start_broadcasting()

            self.lang_managers[lang] = lang_manager
            logger.info(f"Language {lang} added successfully.")
            return True

        logger.warning(f"Language {lang} already exists.")
        return False

    async def start_working_tasks(self):
        logger.info("Starting transcription and broadcasting tasks...")
        self.transcriber.start()
        for lang in self.lang_managers:
            await self.lang_managers[lang].start_broadcasting()

    async def stop_working_tasks(self):
        logger.info("Stopping transcription and broadcasting tasks...")
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
        translated_text = await self.translator.translate_text(
            text=transcription_text,
            target_language=lang
        )
        await self.lang_managers[lang].ws_manager.enqueue_message(translated_text)
