import os
from typing import Dict

from starlette.templating import Jinja2Templates

from app.services.realtime_translation import RealTimeTranslation
from app.utils import generate_version
from app.services.web_socket_broadcast_manager import WebSocketBroadcastManager
from app.services.text_to_speech import GoogleTextToSpeech
from app.services.translators.translator import ITranslator, TranslatorFactory


def get_translator() -> ITranslator:
    from app.config import TRANSLATOR_TYPE

    translator_factory = TranslatorFactory()
    translator_class = translator_factory.get_translator(TRANSLATOR_TYPE)
    return translator_class()

def get_text_to_speech() -> GoogleTextToSpeech:
    return GoogleTextToSpeech()

def get_real_time_translation() -> RealTimeTranslation:
    return RealTimeTranslation(get_translator(), get_text_to_speech())

def get_ws_broadcast_manager() -> WebSocketBroadcastManager:
    return WebSocketBroadcastManager()

def get_jinja_template()-> Jinja2Templates:
    return Jinja2Templates(directory="app/templates")

def get_static_file_versions_for_index_page() -> Dict[str, str]:
    js_file_version = generate_version(os.path.join('/app/static/js/', 'main.js'))
    css_file_version = generate_version(os.path.join('/app/static/css/', 'styles.css'))
    return {"js_file_version": js_file_version, "css_file_version": css_file_version}


def get_static_file_versions_for_admin_page() -> Dict[str, str]:
    js_file_version = generate_version(os.path.join('/app/static/js/', 'settings.js'))
    css_file_version = generate_version(os.path.join('/app/static/css/', 'styles.css'))
    return {"js_file_version": js_file_version, "css_file_version": css_file_version}