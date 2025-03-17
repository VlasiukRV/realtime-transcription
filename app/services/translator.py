import aiohttp
from app.utils import logger

from app.config import GOOGLE_TRANSLATE_API_KEY

google_translate_api_key = GOOGLE_TRANSLATE_API_KEY
google_translate_url = "https://translation.googleapis.com/language/translate/v2"

class Translator:
    def __init__(self):
        """
        Initializes a Translator object with an API key and a target language.

        """
        self.api_key = google_translate_api_key
        self.url = google_translate_url

    async def translate_text(self, text: str, target_language):
        """
        Asynchronous function to translate a given text using Google Translate API.

        :param text: The text to be translated.
        :return: The translated text or an error message if the translation fails.
        @type text: object
        @param target_language: 
        """
        params = {
            "q": text,
            "target": target_language,
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

