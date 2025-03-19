import asyncio
from app.web_socket_manager import WebSocketManager

class LanguageManager:
    def __init__(self, lang: str, create_broadcast_task):
        self.lang = lang
        self.ws_manager = WebSocketManager()
        self.broadcast_task =asyncio.create_task(create_broadcast_task(lang))

    async def stop(self):
        await self.ws_manager.stop_message_broadcasting()
        self.broadcast_task.cancel()