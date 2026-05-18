import asyncio
import threading
from telethon import TelegramClient

class TelethonRunner:
    """
    Обёртка для запуска асинхронного TelegramClient в синхронном окружении (например, Streamlit).
    Создаёт отдельный поток с собственным asyncio event loop, в котором выполняются все корутины.
    Позволяет вызывать асинхронные методы TelegramClient синхронно через метод run().
    """

    def __init__(self, client: TelegramClient):
        """
        Инициализирует экземпляр TelethonRunner.
        Аргументы: client (TelegramClient): экземпляр TelegramClient, который будет использоваться.
        - Создаёт новый asyncio event loop.
        - Запускает фоновый поток, в котором работает event loop.
        - Выполняет подключение клиента к Telegram через self.run(self.client.connect()).
        """
        self.client = client
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.run(self.client.connect())

    def _run_loop(self):
        """
        Внутренний метод, который выполняется в фоновом потоке.
        Устанавливает созданный event loop как текущий для потока и запускает его навечно (run_forever).
        """
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        """
        Синхронно выполняет корутину в фоновом event loop и возвращает её результат.
        Аргументы: coro (coroutine): корутина (асинхронная функция), которую необходимо выполнить.
        Возвращает:  Результат выполнения корутины (тип зависит от переданной корутины).
        """
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def stop(self):
        """
        Корректно завершает работу TelethonRunner:
            - Отключает клиента от Telegram (client.disconnect()).
            - Останавливает event loop фонового потока.
            - Дожидается завершения фонового потока (join).
        """
        self.run(self.client.disconnect())
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._thread.join()