from typing import Any
import json
from pathlib import Path
import os

users_cache: dict[int, Any] = {}

async def get_groups(client: Any) -> list[dict[str, Any]]:
    """
    Получает список всех групп текущего пользователя,
    сохраняет его в файл и возвращает результат.

    Аргументы:
        client (Any): Авторизованный клиент Telegram (TelegramClient).

    Возвращает:
        list[dict[str, Any]]: Список словарей с данными групп (id, name).
    """
    groups = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group or (dialog.is_channel and dialog.entity.megagroup):
            groups.append({
                'id': dialog.id,
                'name': dialog.name
            })
    user = await client.get_me()
    save_json(groups, f"{user.username}_groups.json")
    return groups


async def get_chat_users(client: Any, chat_id: int) -> dict[int, dict[str, Any]]:
    """
    Получает список участников указанного чата, формирует словарь с их данными,
    сохраняет его в файл и возвращает результат.

    Аргументы:
        client (Any): Авторизованный клиент Telegram (TelegramClient).
        chat_id (int): Идентификатор чата.

    Возвращает:
        dict[int, dict[str, Any]]: Словарь, где ключ — ID пользователя (int),
            а значение — словарь с его username и full_name.
    """
    chat_users = {}
    chat = await client.get_entity(chat_id)
    async for user in client.iter_participants(chat):
        first_name = user.first_name if user.first_name else ''
        second_name = user.last_name if user.last_name else ''
        user_name = user.username
        chat_users[int(user.id)] = {
            'username': f"@{user_name}",
            'full_name': first_name + second_name
        }
    user = await client.get_me()
    save_json(chat_users, f"{user.username}_chat_{chat_id}_users.json")
    return chat_users


async def fetch_messages(client: Any, chat_id: int, limit: int = 1000) -> list[dict[str, Any]]:
    """
    Скачивает историю сообщений из чата, извлекает данные (упоминания, реакции),
    сохраняет историю в файл и возвращает список обработанных сообщений.

    Аргументы:
        client (Any): Авторизованный клиент Telegram (TelegramClient).
        chat_id (int): Идентификатор чата.
        limit (int, optional): Максимальное количество сообщений для выгрузки.
            По умолчанию 1000.

    Возвращает:
        list[dict[str, Any]]: Список словарей, каждый из которых содержит
            данные сообщения (m_id, date, sender_id, text, и т.д.).
    """
    chat_users = await get_chat_users(client, chat_id)
    messages = []
    chat = await client.get_entity(chat_id)
    async for m in client.iter_messages(chat, limit=limit):
        if m:
            mentioned = []
            if m.entities:
                for el in m.entities:
                    if hasattr(el, 'user_id'):
                        mentioned.append(el.user_id)
            reactions = []
            if m.reactions:
                for el in m.reactions.results:
                    if hasattr(el.reaction, 'emoticon'):
                        emoji = el.reaction.emoticon
                    elif hasattr(el.reaction, 'document_id'):
                        emoji = f"premium_emoji_{el.reaction.document_id}"
                    else:
                        emoji = 'star_premium_emoji'
                    r_dict = {
                        'type_icon': emoji,
                        'count': el.count
                    }
                    reactions.append(r_dict)
            if m.sender_id in chat_users:
                user_info = chat_users[m.sender_id]
                m_dict = {
                    'm_id': m.id,
                    'date': m.date.isoformat(),
                    'sender_id': m.sender_id,
                    'sender_username': user_info['username'],
                    'sender_full_name': user_info['full_name'],
                    'text': m.text,
                    'reply_m_id': m.reply_to_msg_id,
                    'mentioned_users': mentioned,
                    'reactions': reactions
                }
                messages.append(m_dict)
    user = await client.get_me()
    save_json(messages, f"{user.username}_messages_chat_{chat_id}.json")
    return messages

DATA_DIR = "data"

def ensure_data_dir() -> None:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

def save_json(data: Any, filename: str) -> None:
    """
    Сохраняет переданные данные в файл формата JSON с поддержкой UTF-8.

    Аргументы:
        data (Any): Данные для JSON (обычно list или dict).
        filename (str): Путь к сохраняемому файлу.
    """
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filename: str) -> Any:
    """
    Загружает и десериализует данные из файла формата JSON.

    Аргументы:
        filename (str): Путь к считываемому файлу.

    Возвращает:
        Any: структуры данных Python (обычно list или dict).
    """
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
