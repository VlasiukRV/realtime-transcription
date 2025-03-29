import asyncio

from fastapi import Depends

from app.services.web_socket_broadcast_manager import WebSocketBroadcastManager
from app.utils import logger
from services.dependencies import get_ws_broadcast_manager


class LanguageManager:
    def __init__(self,
                 lang: str,
                 ws_broadcast_manager: WebSocketBroadcastManager = Depends(get_ws_broadcast_manager)
        ):
        self.lang = lang
        self.ws_broadcast_manager = ws_broadcast_manager  # Initialize WebSocket manager
        self.broadcast_task = None  # Initially, the broadcasting task is not started

    async def start_broadcasting(self):
        """
        Method to start broadcasting messages.
        Creates a task for broadcasting messages through WebSocketBroadcastManager.
        """
        if self.broadcast_task is None or self.broadcast_task.done():
            # If the task does not exist or has completed, create a new one
            self.broadcast_task = asyncio.create_task(self.ws_broadcast_manager.start_message_broadcasting())
            logger.info(f"Broadcasting started for language {self.lang}")
        else:
            logger.info(f"Broadcasting is already running for language {self.lang}")

    async def stop(self):
        """Method to stop broadcasting messages and cancel the task."""
        if self.broadcast_task:
            await self.ws_broadcast_manager.stop_message_broadcasting()  # Stop broadcasting messages
            self.broadcast_task.cancel()  # Cancel the broadcast task
            logger.info(f"Broadcasting stopped for language {self.lang}")
        else:
            logger.info(f"No broadcasting task to stop for language {self.lang}")

