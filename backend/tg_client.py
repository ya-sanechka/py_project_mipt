import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
import asyncio

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = "new_session"

proxy_tuple = ('mtproxy.neverspy.online', 443, 'dde8653d2faf392a302d829d79537abbe7')

client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
    connection=ConnectionTcpMTProxyRandomizedIntermediate,
    proxy=proxy_tuple
)

async def authorize():
    if not client.is_connected():
        await client.start()
    return await client.get_me()
