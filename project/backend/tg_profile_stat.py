import os
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest

async def get_my_profile(client: TelegramClient) -> dict:
    """
    Собирает информацию о текущем авторизованном пользователе.

    Аргументы:
        client: авторизованный TelegramClient

    Возвращает:
        dict с ключами:
            - 'id', 'first_name', 'last_name', 'username', 'phone'
            - 'bio': текст "о себе"
            - 'avatar_path': путь к файлу аватарки (выглядит как backend/avatars/avatar_id.png)
            - 'status': строка со статусом (в сети / не в сети) - возвращает UserStatusOnline или UserStatusOffline соответсвенно.
    """
    me = await client.get_me()

    profile = {
        'id': me.id,
        'first_name': me.first_name if me.first_name else '',
        'last_name': me.last_name if me.last_name else '',
        'username': f"@{me.username}" if me.username else None,
        'phone': me.phone,
    }

    try:
        full = await client(GetFullUserRequest(me.id))
        profile['bio'] = full.full_user.about if full.full_user.about else ''
    except Exception:
        profile['bio'] = ''

    avatars_dir = os.path.join('backend', 'avatars')
    avatar_filename = f"avatar_{me.id}.png"
    avatar_path = os.path.join(avatars_dir, avatar_filename)

    if not os.path.exists(avatar_path):
        try:
            await client.download_profile_photo(me.id, file=avatar_path)
        except Exception:
            pass

    if os.path.exists(avatar_path):
        profile['avatar_path'] = avatar_path
    else:
        profile['avatar_path'] = None

    profile['status'] = me.status.to_dict().get('_', 'unknown')

    return profile
