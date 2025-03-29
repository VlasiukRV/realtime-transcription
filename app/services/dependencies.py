from app.services.translators.translator import ITranslator, TranslatorFactory
from services.web_socket_broadcast_manager import WebSocketBroadcastManager


def get_translator() -> ITranslator:
    from app.config import TRANSLATOR_TYPE

    translator_factory = TranslatorFactory()
    translator_class = translator_factory.get_translator(TRANSLATOR_TYPE)
    return translator_class()

def get_ws_broadcast_manager() -> WebSocketBroadcastManager:
    ws_broadcast_manager = WebSocketBroadcastManager()
    return ws_broadcast_manager