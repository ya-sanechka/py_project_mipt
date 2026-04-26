import json

from tg_client import client, authorize
users_cache = {}
async def get_groups():
    await authorize()
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

async def get_chat_users(chat_id):
    await authorize()
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
async def fetch_messages(chat_id, limit=1000):
    chat_users = await get_chat_users(chat_id)
    await authorize()
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
                    else:
                        emoji = f"premium_emoji_{el.reaction.document_id}"
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
                    #мб еще полей добавить
                }
                messages.append(m_dict)
    user = await client.get_me()
    save_json(messages, f"{user.username}_messages_chat_{chat_id}.json")
    return messages

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)