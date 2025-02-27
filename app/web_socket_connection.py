import json
from fastapi import WebSocket, WebSocketDisconnect
from app.utils import logger

BOLD = "\033[1m"
RESET = "\033[0m"

class WebSocketConnection:
    def __init__(self, websocket: WebSocket):
        """
        Initialize the WebSocket connection for a specific client.
        """
        self.websocket = websocket
        self.is_open = True
        self.client_ip, self.client_port = websocket.client
        logger.info(f"{BOLD}Client connected {self.client_ip} port {self.client_port}{RESET}")

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
            print(f"Error sending message: {e}")

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
            await self.websocket.close()
            self.is_open = False
            logger.info(f"Client {self.client_ip} port {self.client_port} disconnected.")
