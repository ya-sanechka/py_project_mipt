import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
import asyncio

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = "new_session"

proxy_tuple = ('168.222.254.174', 443, '968cc5da3ebacdc3f0c99ba9e2d82d07')

client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
    connection=ConnectionTcpMTProxyRandomizedIntermediate,
    proxy=proxy_tuple
)

async def authorize():
    await client.start()
    user = await client.get_me()
    print(f"Successfully {user.first_name} (@{user.username})")

if __name__ == "__main__":
    asyncio.run(authorize())