import asyncio
import json
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from app.utils import logger

BOLD = "\033[1m"
RESET = "\033[0m"

class WebSocketManager:
    def __init__(self):
        """
        Initialize WebSocketManager to handle WebSocket connections,
        manage active clients, and handle broadcasting.
        """
        self.active_clients = set()
        self.mutex_active_clients = asyncio.Lock()  # Renamed to mutex_active_clients

        # Asynchronous queue to store transcriptions
        self.buffer = asyncio.Queue(maxsize=512)
        self.mutex_buffer = asyncio.Lock()

        self.stop_sending_event = asyncio.Event()
        self.stop_sending_event.clear()

    async def broadcast_messages(self):
        """
        Broadcast data from the buffer to all connected WebSocket clients asynchronously.
        """
        self.stop_sending_event.clear()

        while not self.stop_sending_event.is_set():
            await asyncio.sleep(1)

            text = ""
            async with self.mutex_buffer:
                if not self.buffer.empty():
                    # Extract text from the queue with a lock
                    text = await self.buffer.get()

            if not text:
                continue

            # Prepare tasks to send data to all clients
            logger.info(f"Broadcasting data to clients: {text}")
            tasks = []
            disconnected_clients = set()

            async with self.mutex_active_clients:  # Using renamed mutex
                for client in self.active_clients:
                    try:
                        await client.send_text(json.dumps(text, ensure_ascii=False))
                    except websockets.exceptions.ConnectionClosed:
                        disconnected_clients.add(client)

            # Send the messages to all clients
            # if tasks:
            #     await asyncio.sleep(1)
            #     await asyncio.gather(*tasks)  # Send messages to all clients simultaneously

    async def handle_connection(self, websocket: WebSocket):
        """
        Handle WebSocket connections, accept, and manage clients.

        :param websocket: The WebSocket instance representing the client connection.
        """
        await websocket.accept()
        async with self.mutex_active_clients:  # Using renamed mutex
            self.active_clients.add(websocket)  # Add client to the set
            client_ip, client_port = websocket.client
            logger.info(f"{BOLD}Client connected {client_ip} port {client_port}{RESET}")

        try:
            while True:
                await websocket.receive_text()  # Wait for any data from the client (for testing)
        except WebSocketDisconnect:
            logger.info("Client disconnected")
            async with self.mutex_active_clients:  # Using renamed mutex
                self.active_clients.remove(websocket)  # Remove client from the set

    async def enqueue_message(self, text: str):
        """
        Add a message to the buffer queue for broadcasting.

        :param text: The message to be added to the buffer.
        """
        async with self.mutex_buffer:
            await self.buffer.put(text)

    async def start_message_broadcasting(self):
        """
        Start the process of broadcasting messages to all clients.
        """
        await self.broadcast_messages()

    async def stop_message_broadcasting(self):
        """
        Stop the broadcasting process by setting the stop event.
        """
        self.stop_sending_event.set()
    async def disconnect_client(self, websocket: WebSocket):
        """
        Disconnect a client and remove it from the active clients list.

        :param websocket: The WebSocket instance of the client to disconnect.
        """
        async with self.mutex_active_clients:  # Using renamed mutex
            self.active_clients.remove(websocket)  # Remove client from the active clients set

        try:
            await websocket.close()  # Close the WebSocket connection
            logger.info(f"Client {websocket.client} disconnected and WebSocket closed.")
        except Exception as e:
            logger.error(f"Error while disconnecting client {websocket.client}: {e}")

    async def disconnect_clients(self):
        """
        Disconnect all active clients and close their WebSocket connections.
        """
        async with self.mutex_active_clients:  # Using renamed mutex
            tasks = []
            for client in self.active_clients:
                tasks.append(self.disconnect_client(client))  # Call the disconnect_client method for each client
            await asyncio.gather(*tasks)  # Disconnect all clients simultaneously

        logger.info("All clients have been disconnected.")