from collections import defaultdict

from tg_client import authorize
from tg_fetch_message import get_chat_users, fetch_messages, save_json

async def count_messages(chat_id, limit=1000):
    messages = await fetch_messages(chat_id, limit)
    users = await get_chat_users(chat_id)
    message_counter = dict()
    for u in users:
        message_counter[u] = 0
    for m in messages:
        m_sender = m['sender_id']
        message_counter[m_sender] += 1
    message_counter = dict(sorted(message_counter.items(), key=lambda x: x[1], reverse=True))
    return message_counter
