from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.tg_fetch_message import get_chat_users, fetch_messages
from nltk.corpus import stopwords
import pymorphy3
import string

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
        со списком самых активных участников, ключ 'hourly_activity' со статистикой кол-ва
        сообщений по часам, ключ 'weekly_activity' со статистикой по дням недели.
    """
    users_dict = await get_chat_users(client, chat_id)
    messages = await fetch_messages(client, chat_id, limit)
    statistics = {}
    statistics['top10_messages'] = count_messages(messages, users_dict)
    statistics['hourly_activity'] = hourly_activity(messages)
    statistics['top_words'] = top_words(messages)
    statistics['top_phrases'] = calculate_top_phrases(messages, min_count=3, max_words=5, top_n=30)
    #statistics['top_phrases'] = calculate_top_phrases(messages, top_n=20)
    #statistics['top_trigrams'] = calculate_top_trigrams(messages, top_n=20)
    return statistics


def count_messages(messages: List[Dict[str, Any]], users: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def hourly_activity(messages: List[Dict[str, Any]]) -> Dict[int, int]:
    """
    Подсчитывает количество сообщений по часам суток.

    Аргументы:
        messages (List[Dict[str, Any]]): Список словарей с данными сообщений.

    Возвращает:
        Dict[int, int]: Словарь, где ключ — час, значение — количество сообщений.
    """
    hourly = {}
    for msg in messages:
        try:
            dt = datetime.fromisoformat(msg.get('date'))
            hour = dt.hour
            hourly[hour] = hourly.get(hour, 0) + 1
        except (ValueError, KeyError):
            continue

    return hourly


import pymorphy3
def top_words(messages: List[Dict[str, Any]], top_n: int = 20) -> List[Dict[str, Any]]:
    with open('backend/stopwords.txt', 'r', encoding='utf-8') as f:
        stop_words = set(line.strip() for line in f if line.strip())
    morph = pymorphy3.MorphAnalyzer()
    all_words = []
    for msg in messages:
        text = msg.get('text')
        if not text:
            continue
        text = text.lower().translate(str.maketrans('', '', string.punctuation))
        for word in text.split():
            if len(word) >= 4:
                try:
                    if word != 'фпми' and word != 'мфти':
                        lemma = morph.parse(word)[0].normal_form
                    else:
                        lemma = word
                except Exception:
                    lemma = word
                if lemma in stop_words:
                    continue
                all_words.append(lemma)

    freq = {}
    for w in all_words:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda p: p[1], reverse=True)

    top = []
    for word, count in sorted_words[:top_n]:
        if count > 4:
            top.append({'word': word, 'count': count})

    return top

import pymorphy3
import string

def calculate_top_phrases(messages: List[Dict[str, Any]], min_count: int = 3, max_words: int = 5, top_n: int = 20) -> List[Dict[str, Any]]:
    """
    Извлекает самые частые фразы (из n-граммы 2..max_words слов).
    Фраза отбрасывается только если ВСЕ её леммы в stopwords.txt.
    Короткие фразы, полностью входящие в более длинные с близкой частотой, удаляются.

    Аргументы:
        messages: список сообщений
        min_count: минимальное количество вхождений фразы
        max_words: максимальное число слов во фразе (2..5)
        top_n: сколько фраз вернуть
    Возвращает:
        список словарей [{'phrase': '...', 'count': N}, ...]
    """
    with open('backend/stopwords.txt', 'r', encoding='utf-8') as f:
        stop_words = set(line.strip() for line in f if line.strip())

    morph = pymorphy3.MorphAnalyzer()
    all_words = []
    all_original = []

    for msg in messages:
        text = msg.get('text')
        if not text:
            continue
        text = text.lower().translate(str.maketrans('', '', string.punctuation))
        for word in text.split():
            if len(word) < 2:
                continue
            try:
                lemma = morph.parse(word)[0].normal_form
            except Exception:
                lemma = word
            all_words.append(lemma)
            all_original.append(word)

    cnt = {}
    for n in range(2, max_words + 1):
        for i in range(len(all_words) - n + 1):
            lemmas = all_words[i:i+n]
            if len([lemma for lemma in lemmas if lemma in stop_words]) == len(lemmas):
                continue
            phrase = " ".join(all_original[i:i+n])
            cnt[phrase] = cnt.get(phrase, 0) + 1

    cnt = {k: v for k, v in cnt.items() if v >= min_count}

    sorted_phrases = sorted(cnt.items(), key=lambda x: (-len(x[0].split()), -x[1]))
    final = {}
    for phrase, cnt in sorted_phrases:
        words = phrase.split()
        f = True
        for k_phrase, k_cnt in final.items():
            k_words = k_phrase.split()
            if len(k_words) > len(words):
                for j in range(len(k_words) - len(words) + 1):
                    if k_words[j:j+len(words)] == words:
                        if abs(k_cnt - cnt) / max(k_cnt, 1) <= 0.2:
                            f = False
                            break
                if not f:
                    break
        if f:
            final[phrase] = cnt

    result = sorted(final.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{'phrase': phrase, 'count': cnt} for phrase, cnt in result]