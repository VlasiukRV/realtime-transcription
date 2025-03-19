
from app.transcriber import Transcriber
from app.translator import Translator
from app.language_manager import LanguageManager
from app.utils import logger

from pydantic import BaseModel

import asyncio


class LangRequest(BaseModel):
    lang: str


class RealTimeTranslation:
    def __init__(self):

        # Initialize services
        self.transcriber = Transcriber(sample_rate=16000, _handle_transcription=self._handle_transcription)
        self.translator = Translator()

        self.lang_managers: dict[str, LanguageManager] = {}

    async def create_broadcast_task(self, lang: str):
        await self.lang_managers[lang].ws_manager.broadcast_messages()

    async def start_working_tasks(self):
        logger.info("Starting transcription and broadcasting tasks...")
        self.transcriber.start()
        for lang in self.lang_managers:
            self.lang_managers[lang].broadcast_task = asyncio.create_task(self.create_broadcast_task(lang))

    async def stop_working_tasks(self):
        logger.info("Stopping tasks...")
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
