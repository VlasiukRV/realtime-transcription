import asyncio
import websockets
import json
from fastapi import WebSocket, WebSocketDisconnect
from app.utils import logger

BOLD = "\033[1m"
RESET = "\033[0m"

class WebSocketManager:
    def __init__(self):
        """
        Инициализация WebSocketManager для управления соединениями клиентов.
        """
        self.active_clients = set()
        self.mutex_active_clients = asyncio.Lock()  # Мьютекс для управления активными клиентами

        self.buffer = asyncio.Queue(maxsize=512)  # Очередь для сообщений
        self.mutex_buffer = asyncio.Lock()

        self.stop_sending_event = asyncio.Event()
        self.stop_sending_event.clear()

    async def broadcast_messages(self):
        """
        Широковещательная передача данных всем подключенным клиентам.
        """
        self.stop_sending_event.clear()

        while not self.stop_sending_event.is_set():
            await asyncio.sleep(1)

            text = ""
            async with self.mutex_buffer:
                if not self.buffer.empty():
                    text = await self.buffer.get()

            if not text:
                continue

            # Подготовка задач для отправки сообщений всем клиентам
            logger.info(f"Broadcasting data to clients: {text}")
            tasks = []
            async with self.mutex_active_clients:
                for client in self.active_clients:
                    tasks.append(client.send_message(text))

            if tasks:
                await asyncio.gather(*tasks)

    async def handle_connection(self, websocket: WebSocket):
        """
        Обработка WebSocket-соединений и управление клиентами.

        :param websocket: экземпляр WebSocket, представляющий соединение с клиентом.
        """
        await websocket.accept()

        connection = WebSocketConnection(websocket)
        async with self.mutex_active_clients:
            self.active_clients.add(connection)  # Добавление клиента в список активных клиентов

        try:
            while True:
                message = await connection.receive_message()
                if message is None:
                    break  # Прерывание, если соединение закрыто
                # Дополнительная логика для обработки сообщений от клиента
        except WebSocketDisconnect:
            logger.info("Client disconnected.")
        finally:
            await self.disconnect_client(connection)

    async def enqueue_message(self, text: str):
        """
        Добавление сообщения в очередь для широковещательной передачи.

        :param text: Сообщение, которое будет добавлено в очередь.
        """
        async with self.mutex_buffer:
            await self.buffer.put(text)

    async def start_message_broadcasting(self):
        """
        Запуск широковещательной передачи сообщений всем клиентам.
        """
        await self.broadcast_messages()

    async def stop_message_broadcasting(self):
        """
        Остановка процесса передачи сообщений, установив флаг события.
        """
        self.stop_sending_event.set()

    async def disconnect_client(self, connection: WebSocketConnection):
        """
        Отключить клиента и удалить его из активных клиентов.

        :param connection: Экземпляр WebSocketConnection для клиента, которого нужно отключить.
        """
        async with self.mutex_active_clients:
            self.active_clients.remove(connection)

        await connection.close()

    async def disconnect_clients(self):
        """
        Отключить всех активных клиентов и закрыть их WebSocket-соединения.
        """
        async with self.mutex_active_clients:
            tasks = []
            for client in self.active_clients:
                tasks.append(self.disconnect_client(client))
            await asyncio.gather(*tasks)

        logger.info("All clients have been disconnected.")