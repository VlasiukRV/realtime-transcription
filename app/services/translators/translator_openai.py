from collections import deque

from openai import AsyncOpenAI

from app.config import OPEN_AI_KEY
from app.services.translators.translator import ITranslator


def openai_api_key():
    return OPEN_AI_KEY

class OpenAITranslator(ITranslator):
    def __init__(self,
                 api_key: str = openai_api_key()
                 ):
        self.api_key = api_key
        self.context = deque(maxlen=5)

    async def translate_text(self, text: str, language_code: str):

        translated_text = ""
        context_text = "\n".join(self.context)
        self.context.append(text)

        openai = AsyncOpenAI(
            # This is the default and can be omitted
            api_key=self.api_key,
        )

        chat_history = []
        chat_history.append({
                    "role": "system",
                    "content": f"You are a professional literary translator. "
                               f"Translate the following text into {language_code} using a fluent, natural, and contex-aware style."
                               f"Only return the translated sentence"
                    })
        chat_history.append(
            {"role": "user",
             "content": (
                 f"Context:\n{context_text}\n\n"
                 f"Text:\n{text}\n\n"
             )
            }
        )

        # async with httpx.AsyncClient() as client:
        #     response = await client.get("https://example.com")

        # gpt - 4 - turbo
        response = await openai.responses.create(
            model="gpt-4-turbo",
            input=chat_history,
        )

        translated_text = response.output_text

        return translated_text