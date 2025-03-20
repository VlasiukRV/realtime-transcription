import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.utils import logger
from app.services.web_socket_connection import WebSocketConnection

BOLD = "\033[1m"
RESET = "\033[0m"

class WebSocketManager:
    def __init__(self):
        """
        Initialize WebSocketManager to manage client connections.
        """
        self.active_clients = set()
        self.mutex_active_clients = asyncio.Lock()  # Mutex for managing active clients

        self.buffer = asyncio.Queue(maxsize=512)  # Queue for messages
        self.mutex_buffer = asyncio.Lock()

        self.stop_sending_event = asyncio.Event()
        self.stop_sending_event.clear()

    def has_active_clients(self) -> bool:
        """
        Method to check if there are any active clients.

        Returns:
            bool: True if there are active clients, False otherwise.
        """
        return len(self.active_clients) > 0

    async def start_message_broadcasting(self):
        """
        Broadcast messages to all connected clients.
        """
        self.stop_sending_event.clear()

        while not self.stop_sending_event.is_set():
            await asyncio.sleep(1)
            await self._broadcast_messages_logic()


    async def _broadcast_messages_logic(self):
        text = await self._get_message_from_queue()

        if not text:
            return

        # Remove clients with is_open == False
        async with self.mutex_active_clients:
            self.active_clients = set(client for client in self.active_clients if client.is_open)

        # Prepare tasks for sending messages to all clients
        logger.info(f"Broadcasting data to clients: {text}")
        tasks = []
        async with self.mutex_active_clients:
            for client in self.active_clients:
                tasks.append(client.send_message(text))

        if tasks:
            await asyncio.gather(*tasks)

    async def _get_message_from_queue(self):
        async with self.mutex_buffer:
            if not self.buffer.empty():
                return await self.buffer.get()
        return ""

    async def handle_connection(self, websocket: WebSocket):
        """
        Handle WebSocket connections and manage clients.

        :param websocket: WebSocket instance representing the client connection.
        """
        await websocket.accept()

        connection = WebSocketConnection(websocket)
        async with self.mutex_active_clients:
            self.active_clients.add(connection)  # Add client to the active clients list

        try:
            while True:
                message = await connection.receive_message()
                if message is None:
                    break  # Break if the connection is closed
                # Additional logic to process messages from the client
        except WebSocketDisconnect:
            logger.info("Client disconnected.")
        finally:
            await self.disconnect_client(connection)

    async def enqueue_message(self, text: str):
        """
        Add a message to the queue for broadcasting.

        :param text: The message to be added to the queue.
        """
        async with self.mutex_buffer:
            await self.buffer.put(text)

    async def stop_message_broadcasting(self):
        """
        Stop the message broadcasting process by setting the event flag.
        """
        self.stop_sending_event.set()

    async def disconnect_client(self, connection: WebSocketConnection):
        """
        Disconnect a client and remove them from the active clients.

        :param connection: WebSocketConnection instance of the client to disconnect.
        """
        async with self.mutex_active_clients:
            self.active_clients.remove(connection)

        await connection.close()

    async def disconnect_clients(self):
        """
        Disconnect all active clients and close their WebSocket connections.
        """
        async with self.mutex_active_clients:
            tasks = []
            for client in self.active_clients:
                tasks.append(self.disconnect_client(client))
            await asyncio.gather(*tasks)

        logger.info("All clients have been disconnected.")
