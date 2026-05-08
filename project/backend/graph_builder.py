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

    metrics = compute_metrics(G)

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
        'metrics': metrics
    }


def compute_metrics(G):
    """
    Вычисляет основные метрики графа, используя переданный ориентированный граф взаимодействий G.

    Аргументы функции:
        G: ориентированный граф networkx

    Возвращает:
        dict с ключами:
            - 'nodes_count': общее количество узлов (участников)
            - 'edges_count': общее количество направленных рёбер (связей)
            - 'density': плотность графа (от 0 до 1, где 1 = клика)
            - 'strongly_connected_components': список КСС, каждая компонента — dict с ключами 'size' и 'members'
            (оставляем только компоненты с размером > 1)
            - 'articulation_points': список id участников - точек сочленения (люди, при удалении которых граф перестает быть связным)
            - 'bridges': список мостов — пары людей, при удалении связи между которыми граф перестает быть связным.
            - 'top_central_users': список из 10 самых центральных участников по степени (degree centrality), каждый элемент — dict с ключами 'user_id' и 'centrality': степень центральности (от 0 до 1)
    """
    metrics = {}
    #везде ниже когда работаем с узлом как с интом, там лежит айдишник пользователя :)))

    # число точек, ребер, плотность связей в графе
    metrics['nodes_count'] = G.number_of_nodes()
    metrics['edges_count'] = G.number_of_edges()
    metrics['density'] = round(nx.density(G), 4) # считает плотность графа от 0 до 1, где 1 - клика

    # ищем компоненты сильной связности
    KSS_list = list(nx.strongly_connected_components(G)) #список КСС
    groups_components = []
    for comp in KSS_list:
        if len(comp) > 1:
            members = []
            for x in comp:
                members.append(int(x))
            groups_components.append({
                'size': len(comp),
                'members': members
            })
    metrics['strongly_connected_components'] = groups_components


    undirected_G = G.to_undirected() # делаем неоритентироанную копию для поиска некоторых метрик

    # ищем точки сочленения (неориентированный граф)
    articulation_points = list(nx.articulation_points(undirected_G)) #точки сочлененения
    ap_list = []
    for x in articulation_points:
        ap_list.append(int(x))
    metrics['articulation_points'] = ap_list

    # ищем мосты (неориентированный граф)
    bridges = list(nx.bridges(undirected_G))
    bridge_pairs = []
    for u, v in bridges:
        bridge_pairs.append((int(u), int(v)))
    metrics['bridges'] = bridge_pairs

    # ищем топ 10 центральных узлов-юзеров (степень центральности = доля существующих связей от всевозможных)
    degree_cent = nx.degree_centrality(G)
    cent_items = []
    for user, deg in degree_cent.items():
        cent_items.append((user, deg))
    cent_items.sort(key=lambda pair: pair[1], reverse=True)
    top_users = []
    for user, deg in cent_items[:10]:
        top_users.append({
            'user_id': int(user),
            'centrality': round(deg, 4)
        })
    metrics['top_central_users'] = top_users

    return metrics