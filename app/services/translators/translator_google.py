import aiohttp
from fastapi import Depends

from app.utils import logger
from app.config import GOOGLE_API_KEY
from app.services.translators.translator import ITranslator

def google_api_key():
    return GOOGLE_API_KEY

def google_text_to_speach_url():
 return "https://translation.googleapis.com/language/translate/v2"

class GoogleTranslatorHTTP(ITranslator):
    def __init__(self,
                 api_key: str = google_api_key(),
                 url: str = google_text_to_speach_url()
                 ):
        """
        Initializes a Translator object with an API key and a target language.

        """
        self.api_key = api_key
        self.url = url

    async def translate_text(self, text: str, language_code: str):
        """
        Asynchronous function to translate a given text using Google Translate API.

        :param text: The text to be translated.
        :param language_code:
        :return: The translated text or an error message if the translation fails.
        @type text: object
        @param language_code:
        """
        params = {
            "q": text,
            "target": language_code,
            "key": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, params=params) as response:
                    response.raise_for_status()  # Raises an exception for 4xx/5xx HTTP errors
                    result = await response.json()
                    # Extract the translated text from the API response
                    return result['data']['translations'][0]['translatedText']
        except aiohttp.ClientResponseError as e:
            logger.error(f"Translation API error: {e}")
            return "Translation error"
        except Exception as e:
            logger.error(f"An error occurred during translation: {e}")
            return "Translation failed"

