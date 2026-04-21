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
    await client.start()
    user = await client.get_me()
    print(f"Successfully {user.first_name} (@{user.username})")


async def get_groups():
    groups = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group or (dialog.is_channel and dialog.entity.megagroup):
            groups.append({
                'id': dialog.id,
                'name': dialog.name
            })
    return groups

async def main():
    await authorize()
    groups = await get_groups()
    print("\nСписок групп:")
    i = 1
    for g in groups:
        print(f"{i}. ID: {g['id']} название: {g['name']}")
        i += 1

if __name__ == "__main__":
    asyncio.run(main())