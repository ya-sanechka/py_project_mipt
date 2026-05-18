from typing import Any, Dict, List, Optional
from backend.tg_fetch_message import get_chat_users, fetch_messages


async def get_statistic(client: Any, chat_id: int, limit: int = 1000) -> Dict[str, Any]:
    """
    Получает список пользователей и сообщения чата, после чего рассчитывает
    статистику топ-10 самых активных участников.

    Аргументы:
        client (Any): Авторизованный клиент Telegram (например, TelegramClient).
        chat_id (int): Идентификатор чата.
        limit (int, optional): Максимальное количество последних сообщений для анализа. По умолчанию 1000.

    Возвращает:
        Dict[str, Any]: Словарь со статистикой чата, содержащий ключ 'top10_messages'
        со списком самых активных участников.
    """
    users_dict = await get_chat_users(client, chat_id)
    messages = await fetch_messages(client, chat_id, limit)
    statistics= {}
    statistics['top10_messages'] = await count_messages(messages, users_dict)
    return statistics


async def count_messages(messages: List[Dict[str, Any]], users: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Подсчитывает количество сообщений от каждого пользователя и формирует
    рейтинг из 10 самых активных участников чата.

    Аргументы:
        messages (List[Dict[str, Any]]): Список словарей с данными сообщений.
        users (Dict[int, Dict[str, Any]]): Словарь зарегистрированных участников чата,

    Возвращает:
        List[Dict[str, Any]]: Список из 10 словарей, содержащих статистику
        активных пользователей (user_id, full_name, count, percent), отсортированный
        по убыванию активности.
    """
    message_counter = {}
    for u in users:
        message_counter[u] = {
            'count': 0,
            'percent': 0,
        }

    tot_cnt = 0
    for m in messages:
        m_sender = m.get('sender_id')
        if m_sender in message_counter:
            tot_cnt += 1
            message_counter[m_sender]['count'] += 1

    if tot_cnt == 0:
        return []

    sorted_count = sorted(message_counter.items(), key=lambda x: x[1]['count'], reverse=True)

    top10_list = []
    for u, data in sorted_count[:10]:
        if data['count'] > 0:
            data['percent'] = data['count'] / tot_cnt
            user_info = users.get(u, {})
            full_name = user_info.get('full_name', f"id{u}")
            top10_list.append({
                'user_id': u,
                'full_name': full_name,
                'count': data['count'],
                'percent': data['percent']
            })

    return top10_list
