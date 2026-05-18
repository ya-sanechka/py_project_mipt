import os
from typing import Dict, Union
from pathlib import Path

from dotenv import load_dotenv
from pip._internal.utils.misc import ensure_dir
from telethon import TelegramClient
from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError,
    FloodWaitError,
)

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

proxy_tuple = ('mtproxy.neverspy.online', 443, 'dde8653d2faf392a302d829d79537abbe7')

SESSIONS_DIR = "sessions"

def create_client(session_name: str = "new_session") -> TelegramClient:
    """
    Создаёт новый экземпляр TelegramClient с указанным именем сессии.
    """
    ensure_dir(SESSIONS_DIR)
    session_path = os.path.join(SESSIONS_DIR, session_name)
    return TelegramClient(
        session_path,
        API_ID,
        API_HASH,
        connection=ConnectionTcpMTProxyRandomizedIntermediate,
        proxy=proxy_tuple,
    )


async def request_code(client: TelegramClient, phone: str) -> Dict[str, Union[str, int, float]]:
    """
    Авторизация (1 шаг) - Отправляет код подтверждения на указанный номер телефона.

    Аргументы функции:
        client: TelegramClient
        phone: номер телефона (строка типа '+7...').

    Возвращает:
        Словарь с ключами:
            - status: 'code_sent' или 'error'
            - message: описание результата
            - timeout: время ожидания до повторного запроса кода (если не придет)
            - phone_code_hash: хэш, нужен для входа
            - error_type: тип ошибки (если status='error')
            - wait_seconds: сколько секунд нужно подождать при flood_wait ошибке
    """
    if not client.is_connected():
        await client.connect()
    try:
        result = await client.send_code_request(phone)
        return {
            "status": "code_sent",
            "message": f"Код отправлен на {phone}",
            "timeout": result.timeout,
            "phone_code_hash": result.phone_code_hash,
        }
    except PhoneNumberInvalidError:
        return {
            "status": "error",
            "error_type": "invalid_phone",
            "message": "Неверный номер телефона.",
        }
    except FloodWaitError as e:
        return {
            "status": "error",
            "error_type": "flood_wait",
            "message": f"Слишком много попыток. Подождите {e.seconds} секунд.",
            "wait_seconds": e.seconds,
        }


async def sign_in(client: TelegramClient, phone: str, code: str, phone_code_hash: str) -> Dict[str, Union[str, None]]:
    """
    Авторизация (2 шаг): выполняет вход по коду подтверждения.
    Если аккаунт защищён двухфакторной аутентификацией, возвращает статус 'password_needed'.

    Аргументы функции:
        client: TelegramClient.
        phone: номер телефона.
        code: код подтверждения из Telegram.
        phone_code_hash: хэш, полученный от request_code.

    Возвращает:
        Словарь с ключами:
            - status: 'authorized' / 'password_needed' / 'error'
            - user: строка вида "Имя (@username)" при успехе
            - message: описание
            - error_type: тип ошибки (при status='error')
            - wait_seconds: сколько ждать секунд при flood_wait
    """
    if not client.is_connected():
        await client.connect()



    try:
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        me = await client.get_me()
        return {
            "status": "authorized",
            "user": f"{me.first_name} (@{me.username})",
        }
    except PhoneCodeInvalidError:
        return {
            "status": "error",
            "error_type": "invalid_code",
            "message": "Неверный код подтверждения. Попробуйте ещё раз.",
        }
    except PhoneCodeExpiredError:
        return {
            "status": "error",
            "error_type": "code_expired",
            "message": "Срок действия кода истёк. Запросите новый код.",
        }
    except SessionPasswordNeededError:
        return {
            "status": "password_needed",
            "message": "Требуется пароль двухфакторной аутентификации",
        }
    except FloodWaitError as e:
        return {
            "status": "error",
            "error_type": "flood_wait",
            "message": f"Слишком много попыток. Подожди {e.seconds} секунд.",
            "wait_seconds": e.seconds,
        }


async def send_password(client: TelegramClient, password: str) -> Dict[str, Union[str, None]]:
    """
    Авторизация (3 шаг) (при необходимости пароля): отправляет пароль двухфакторной аутентификации.

    Аргументы функции:
        client: TelegramClient.
        password: пароль двухфакторной аутентификации.

    Возвращает:
        Словарь с ключами:
            - status: 'authorized' / 'error'
            - user: пользователь, при успехе
            - message: описание
            - error_type: тип ошибки (при status='error')
            - wait_seconds: при flood_wait
    """
    if not client.is_connected():
        await client.connect()

    try:
        await client.sign_in(password=password)
        me = await client.get_me()
        return {
            "status": "authorized",
            "user": f"{me.first_name} (@{me.username})",
        }
    except PasswordHashInvalidError:
        return {
            "status": "error",
            "error_type": "invalid_password",
            "message": "Неверный пароль. Попробуй ещё раз.",
        }
    except FloodWaitError as e:
        return {
            "status": "error",
            "error_type": "flood_wait",
            "message": f"Слишком много попыток. Подожди {e.seconds} секунд.",
            "wait_seconds": e.seconds,
        }


async def tg_authorized(client: TelegramClient):  #возвращает объект типа User

    """
    Проверяет, авторизован ли клиент, и возвращает объект текущего пользователя.
    Иначе вызывает исключение.

    Аргументы функции:
        client: TelegramClient.

    Возвращает:
        Объект User с информацией о текущем пользователе.

    Exception: если пользователь не авторизован.
    """
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        raise Exception("Пользователь не авторизован.")
    return await client.get_me()