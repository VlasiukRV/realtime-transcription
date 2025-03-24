import json
from fastapi import WebSocket, WebSocketDisconnect
from app.utils import logger

BOLD = "\033[1m"
RESET = "\033[0m"

class WebSocketConnection:
    def __init__(self,
                 websocket: WebSocket,
                 disconnect_func = None,
                 on_message_func = None
    ):
        """
        Initialize the WebSocket connection for a specific client.
        """
        self.websocket = websocket
        self.is_open = True
        self.client_ip, self.client_port = websocket.client

        self.disconnect_func = disconnect_func
        self.on_message_func = on_message_func

    async def accept(self):
        """
        Accept the WebSocket connection from the client.
        """
        try:
            await self.websocket.accept()  # Accept the WebSocket connection
            self.is_open = True
            logger.info(f"{BOLD}WebSocket connection accepted for {self.client_ip}:{self.client_port}{RESET}")
            await self._process_messages()
        except WebSocketDisconnect:
            self.is_open = False
            logger.info("Client disconnected.")
        except Exception as e:
            self.is_open = False
            logger.error(f"Error accepting WebSocket connection: {e}")
        finally:
            await self.close()

    async def _process_messages(self):
        """
        Process incoming messages from the client.
        """
        try:
            while self.is_open:
                message = await self.receive_message()
                if message and self.on_message_func:
                    self.on_message_func(message)
        except WebSocketDisconnect:
            self.is_open = False
        except Exception as e:
            self.is_open = False

    async def send_message(self, message: str):
        """
        Method for sending messages to the client.
        """
        try:
            if self.is_open:
                await self.websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            # Error while sending - closing the connection
            self.is_open = False
            # Logging the error (could be replaced with a more advanced logger)
            logger.info(f"Error sending message: {e}")

    async def receive_message(self):
        """
        Method for receiving messages from the client.
        """
        if self.is_open:
            try:
                return await self.websocket.receive_text()
            except WebSocketDisconnect:
                self.is_open = False
                return None

    async def close(self):
        """
        Close the WebSocket connection with the client.
        """
        if self.is_open:
            try:
                await self.websocket.close()
                self.is_open = False
                logger.info(f"Client {self.client_ip} port {self.client_port} disconnected.")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
            self.disconnect_func(self)
