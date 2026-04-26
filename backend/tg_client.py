import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError,
    FloodWaitError
)

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = "new_session"

proxy_tuple = ('mtproxy.neverspy.online', 443, 'dde8653d2faf392a302d829d79537abbe7')

def create_client():
    return TelegramClient(
        "new_session",
        API_ID,
        API_HASH,
        connection=ConnectionTcpMTProxyRandomizedIntermediate,
        proxy=proxy_tuple
    )


async def request_code(client, phone):
    if not client.is_connected():
        await client.connect()
    try:
        result = await client.send_code_request(phone)
        return {
            "status": "code_sent",
            "message": f"Код отправлен на {phone}",
            "timeout": result.timeout,
            "phone_code_hash": result.phone_code_hash
        }
    except PhoneNumberInvalidError:
        return {
            "status": "error",
            "error_type": "invalid_phone",
            "message": "Неверный номер телефона."
        }
    except FloodWaitError as e:
        return {
            "status": "error",
            "error_type": "flood_wait",
            "message": f"Слишком много попыток. Подождите {e.seconds} секунд.",
            "wait_seconds": e.seconds
        }

async def sign_in(client, phone, code, phone_code_hash):
    if not client.is_connected():
        await client.connect()

    try:
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        me = await client.get_me()
        return {
            "status": "authorized",
            "user": f"{me.first_name} (@{me.username})"
        }
    except PhoneCodeInvalidError:
        return {
            "status": "error",
            "error_type": "invalid_code",
            "message": "Неверный код подтверждения. Попробуйте ещё раз."
        }
    except PhoneCodeExpiredError:
        return {
            "status": "error",
            "error_type": "code_expired",
            "message": "Срок действия кода истёк. Запросите новый код."
        }
    except SessionPasswordNeededError:
        return {
            "status": "password_needed",
            "message": "Требуется пароль двухфакторной аутентификации"
        }
    except FloodWaitError as e:
        return {
            "status": "error",
            "error_type": "flood_wait",
            "message": f"Слишком много попыток. Подожди {e.seconds} секунд.",
            "wait_seconds": e.seconds
        }


async def send_password(client, password):
    if not client.is_connected():
        await client.connect()

    try:
        await client.sign_in(password=password)
        me = await client.get_me()
        return {
            "status": "authorized",
            "user": f"{me.first_name} (@{me.username})"
        }
    except PasswordHashInvalidError:
        return {
            "status": "error",
            "error_type": "invalid_password",
            "message": "Неверный пароль. Попробуй ещё раз."
        }
    except FloodWaitError as e:
        return {
            "status": "error",
            "error_type": "flood_wait",
            "message": f"Слишком много попыток. Подожди {e.seconds} секунд.",
            "wait_seconds": e.seconds
        }


async def tg_authorized(client):
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        raise Exception("Пользователь не авторизован.")
    return await client.get_me()
