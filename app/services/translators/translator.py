from abc import ABC, abstractmethod
from typing import List, Type
from enum import Enum

class TranslatorType(Enum):
    GOOGLE = "google"

class ITranslator(ABC):
    @abstractmethod
    async def translate_text(self, text: str, language_code: str) -> str:
        """
        Abstract method to translate text to the target language.

        :param text: The text to be translated.
        :param language_code: The language code to translate the text into.
        :return: The translated text.
        """
        pass

class TranslatorFactory:

    def get_translator(self, translator_type: TranslatorType) -> Type[ITranslator]:
        from app.services.translators.translator_google import GoogleTranslatorHTTP

        return GoogleTranslatorHTTP

        # if translator_type == TranslatorType.GOOGLE:
        #
        #    return GoogleTranslator_HTTP
        #else:
        #    raise ValueError(f"Unknown translator type: {translator_type}")
