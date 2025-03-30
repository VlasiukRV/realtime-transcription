import base64
import os
import asyncio

from google.cloud import texttospeech
from google.oauth2 import service_account

def get_google_key_path():
    return  os.path.join(os.getcwd(), 'google_service_account_file.json')


class GoogleTextToSpeech:
    def __init__(self,
                 key_path:str = get_google_key_path()):
        """
        Initializes the client for interacting with Google Text-to-Speech API.
        :param key_path: Path to the JSON file containing the service account key
        """
        self.client = texttospeech.TextToSpeechClient(
            credentials=service_account.Credentials.from_service_account_file(key_path)
        )

    async def text_to_speech(self, text: str, language_code: str):
        audio_content = self.synthesize_speech(text, language_code)
        await asyncio.sleep(1)
        return base64.b64encode(audio_content).decode('utf-8')

    def synthesize_speech(self,
                          text: str,
                          language_code: str = "en-US",
                          ssml_gender="MALE",
                          audio_format="MP3",
                          pitch=0.0,
                          speaking_rate=1.0,
                          volume_gain_db=5.0,
                          voice_name=None):
        """
        Converts text to speech and saves it as an audio file.

        :param text: Text to be converted into speech
        :param language_code: Language and region code (e.g., "en-US" for English, US)
        :param ssml_gender: Voice gender ("NEUTRAL", "MALE", "FEMALE")
        :param audio_format: Audio format ("MP3" or "LINEAR16")
        """
        # Create a SynthesisInput object with the text
        synthesis_input = texttospeech.SynthesisInput(text=text)
        if not voice_name:
            voice_name = "ru-RU-Wavenet-D"

        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=self._get_ssml_gender(ssml_gender),
            name=voice_name
        )

        # Set up the audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=self._get_audio_encoding(audio_format),
            pitch=pitch,  # Регулировка тона
            speaking_rate=speaking_rate,  # Регулировка скорости речи
            volume_gain_db=volume_gain_db    # Регулировка громкости
        )

        # Call the API to synthesize speech
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        return response.audio_content

    def _get_ssml_gender(self, gender: str):
        """
        Returns the corresponding SSML gender type based on the given parameter.
        :param gender: Voice gender ("NEUTRAL", "MALE", "FEMALE")
        :return: Corresponding SsmlVoiceGender type
        """
        gender_map = {
            "NEUTRAL": texttospeech.SsmlVoiceGender.NEUTRAL,
            "MALE": texttospeech.SsmlVoiceGender.MALE,
            "FEMALE": texttospeech.SsmlVoiceGender.FEMALE
        }
        return gender_map.get(gender.upper(), texttospeech.SsmlVoiceGender.NEUTRAL)

    def _get_audio_encoding(self, audio_format: str):
        """
        Returns the corresponding audio encoding type based on the given parameter.
        :param audio_format: Audio format ("MP3", "LINEAR16")
        :return: Corresponding AudioEncoding type
        """
        format_map = {
            "MP3": texttospeech.AudioEncoding.MP3,
            "LINEAR16": texttospeech.AudioEncoding.LINEAR16
        }
        return format_map.get(audio_format.upper(), texttospeech.AudioEncoding.MP3)
