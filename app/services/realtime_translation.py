import json

from fastapi import WebSocket, Depends
import asyncio
from typing import Dict

from app.services.transcribers.transcriber import Transcriber
from app.services.translators.translator import ITranslator
from app.services.language_manager import LanguageBroadcastManager
from app.utils import logger
from app.services.text_to_speech import GoogleTextToSpeech
from services.web_socket_broadcast_manager import WebSocketBroadcastManager

class RealTimeTranslation:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 translator: ITranslator,
                 tts: GoogleTextToSpeech
    ):
        # Initialize services
        if not hasattr(self, 'initialized'):  # Protecting from re-initialization
            self.transcriber = Transcriber(sample_rate=16000, _handle_transcription=self._handle_transcription)

            self.translator = translator
            self.tts = tts

            self.lang_managers: Dict[str, LanguageBroadcastManager] = {}

            # Mark as initialized
            self.initialized = True

    async def handle_websocket_connection(self, lang: str, websocket: WebSocket) -> bool:
        """
        Handle WebSocket connection for a specific language.
        """
        if lang not in self.lang_managers:
            return False

        broadcast_manager = self.__get_broadcast_manager(lang)
        await broadcast_manager.handle_connection(websocket)
        return True

    async def add_language(self, lang: str, ws_broadcast_manager: WebSocketBroadcastManager) -> bool:
        """
        Add a new language for translation and processing.
        """
        if lang not in self.lang_managers:
            lang_manager = LanguageBroadcastManager(lang, ws_broadcast_manager)
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
            language_manager = self.__get_language_manager(lang)
            await language_manager.start_broadcasting()

    async def stop_working_tasks(self):
        """
        Stop all transcription and broadcasting tasks.
        """
        logger.info("\033[33mStopping transcription and broadcasting tasks...\033[0m")
        for lang in list(self.lang_managers.keys()):
            language_manager = self.__get_language_manager(lang)
            await language_manager.stop()
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
            language_code=lang
        )

        audio_content = await self.tts.text_to_speech(
             text=translated_text,
             language_code=lang
         )

        message_data = {
            "lang": lang,
            "original_text": transcription_text,
            "translated_text": translated_text,
            "audio_content": audio_content
        }
        # message_json = json.dumps(message_data, ensure_ascii=False)

        broadcast_manager = self.__get_broadcast_manager(lang)
        await broadcast_manager.enqueue_message(message_data)

    def __get_broadcast_manager(self, lang: str) -> WebSocketBroadcastManager:
        return self.lang_managers[lang].ws_broadcast_manager

    def __get_language_manager(self, lang: str) -> LanguageBroadcastManager:
        return self.lang_managers[lang]
