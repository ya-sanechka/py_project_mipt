import networkx as nx
from tg_fetch_message import get_chat_users, fetch_messages

async def build_graph(client, chat_id, limit=1000):
    """
    Строит граф взаимодействий для указанного чата.
    Аргументы функции:
        client: авторизованный TelegramClient
        chat_id: id группы
        limit: лимит, сколько последних сообщений обработать
    Возвращает:
        dict с ключами:
            - 'nodes': список узлов (словари с id, full_name, username)
            - 'edges': список рёбер (sender, target, weight, replied, mentioned)
            - 'metrics': словарь с метриками графа
    """
    users_dict = await get_chat_users(client, chat_id)
    messages = await fetch_messages(client, chat_id, limit)
    G = nx.DiGraph()

    for user_id, info in users_dict.items():
        full_name = info.get('full_name')
        if not full_name:
            full_name = f"id{user_id}"
        G.add_node(int(user_id), full_name=full_name, username=info.get('username'))

    edges = {}

    msg_senders = {}
    for msg in messages:
        sender = msg.get('sender_id')
        m_id = msg.get('m_id')
        if sender is not None and m_id is not None:
            msg_senders[m_id] = sender

    for msg in messages:
        sender = msg.get('sender_id')
        if sender is not None:
            msg_reply = msg.get('reply_m_id')
            if msg_reply is not None and msg_reply in msg_senders:
                replier = msg_senders[msg_reply]
                if replier != sender:
                    k = (sender, replier)
                    if k not in edges:
                        edges[k] = {'replied': 0, 'mentioned': 0}
                    edges[k]['replied'] += 1
            mentioned_users = msg.get('mentioned_users', [])
            for mentioned_id in mentioned_users:
                if mentioned_id != sender:
                    k = (sender, mentioned_id)
                    if k not in edges:
                        edges[k] = {'replied': 0, 'mentioned': 0}
                    edges[k]['mentioned'] += 1

    for (snd, trg), data in edges.items():
        G.add_edge(snd, trg, weight=data['replied'] + data['mentioned'],
                   replied=data['replied'], mentioned=data['mentioned'])



    nodes_list = []
    for node in G.nodes():
        node_info = {
            'id': node,
            'full_name': G.nodes[node].get('full_name'),
            'username': G.nodes[node].get('username')
        }
        nodes_list.append(node_info)

    edges_list = []
    for u, v, data in G.edges(data=True):
        edge_info = {
            'sender': u,
            'target': v,
            'weight': data['replied'] + data['mentioned'],
            'replied': data['replied'],
            'mentioned': data['mentioned']
        }
        edges_list.append(edge_info)

    return {
        'nodes': nodes_list,
        'edges': edges_list,
        # 'metrics': metrics
    }
