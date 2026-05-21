import networkx as nx
from backend.tg_fetch_message import get_chat_users, fetch_messages

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
                        edges[k] = {'replied': 0, 'mentioned': 0, 'rapid_answer': 0}
                    edges[k]['replied'] += 1
            mentioned_users = msg.get('mentioned_users', [])
            for mentioned_id in mentioned_users:
                if mentioned_id != sender:
                    k = (sender, mentioned_id)
                    if k not in edges:
                        edges[k] = {'replied': 0, 'mentioned': 0, 'rapid_answer': 0}
                    edges[k]['mentioned'] += 1

    from datetime import datetime, timedelta, timezone
    def parse_date(msg):
        try:
            return datetime.fromisoformat(msg['date'])
        except Exception:
            return None

    dated_messages = [msg for msg in messages if parse_date(msg) is not None]
    dated_messages.sort(key=lambda m: parse_date(m))

    for i in range(1, len(dated_messages)):
        prev = dated_messages[i - 1]
        curr = dated_messages[i]
        prev_sender = prev.get('sender_id')
        curr_sender = curr.get('sender_id')

        if prev_sender is None or curr_sender is None:
            continue
        if prev_sender == curr_sender:
            continue
        if curr.get('reply_m_id') == prev.get('m_id'):
            continue

        prev_time = parse_date(prev)
        curr_time = parse_date(curr)
        if prev_time is None or curr_time is None:
            continue
        delta = (curr_time - prev_time).total_seconds()
        if 0 < delta <= 60:
            k = (curr_sender, prev_sender)
            if k not in edges:
                edges[k] = {'replied': 0, 'mentioned': 0, 'rapid_answer': 0}
            edges[k]['rapid_answer'] += 1

    for (snd, trg), data in edges.items():
        G.add_edge(snd, trg, weight=data['replied'] + data['mentioned'],
                   replied=data['replied'], mentioned=data['mentioned'], rapid_answer=data['rapid_answer'])

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
            'weight': 2 * data['replied'] + data['mentioned'] + data['rapid_answer'],
            'replied': data['replied'],
            'mentioned': data['mentioned'],
            'rapid_answer': data['rapid_answer']
        }
        edges_list.append(edge_info)

    return {
        'nodes': nodes_list,
        'edges': edges_list,
        'metrics': metrics,
        'users': users_dict
    }

import networkx as nx
import networkx.algorithms.community as nx_comm

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
            - 'giant_component_ratio': доля участников, состоящих в основном ядре обсуждения
            - 'communities': список сообществ (алгоритм Лувена), каждое компонента — dict с ключами 'community_id', 'size' и 'members'
            - 'top_central_users': список из 10 самых центральных участников по степени (degree centrality)
            - 'top_pagerank': список из 10 самых авторитетных участников по PageRank
            - 'top_betweenness': список из 10 главных связующих звеньев (betweenness centrality)
            - 'articulation_points': список id участников - точек сочленения
            - 'bridges': список мостов — пары людей, при удалении связи между которыми граф перестает быть связным
    """
    metrics = {}

    metrics['nodes_count'] = G.number_of_nodes()
    metrics['edges_count'] = G.number_of_edges()
    metrics['density'] = round(nx.density(G), 4)

    if metrics['edges_count'] == 0:
        return metrics

    wcc_list = list(nx.weakly_connected_components(G))
    if wcc_list:
        largest_wcc = max(wcc_list, key=len)
        metrics['giant_component_ratio'] = round(len(largest_wcc) / metrics['nodes_count'], 4)
    else:
        metrics['giant_component_ratio'] = 0

    undirected_G = G.to_undirected()

    communities = nx_comm.louvain_communities(undirected_G, weight='weight')
    group_components = []
    for i, с in enumerate(communities):
        if len(с) > 1:
            members = []
            for x in с:
                members.append(int(x))
            group_components.append({
                'community_id': i,
                'size': len(с),
                'members': members
            })
    group_components.sort(key=lambda x: x['size'], reverse=True)
    metrics['communities'] = group_components


    degree_cent = nx.degree_centrality(G)
    cent_p = []
    for user, deg in degree_cent.items():
        cent_p.append((user, deg))
    cent_p.sort(key=lambda p: p[1], reverse=True)
    top_users = []
    for user, deg in cent_p[:10]:
        top_users.append({
            'user_id': int(user),
            'centrality': round(deg, 4)
        })
    metrics['top_central_users'] = top_users

    pagerank_stat = nx.pagerank(G, weight='weight', max_iter=100)
    pagerank_p = []
    for user, v in pagerank_stat.items():
        pagerank_p.append((user, v))
    pagerank_p.sort(key=lambda p: p[1], reverse=True)
    top_pr = []
    for user, v in pagerank_p[:10]:
        top_pr.append({
            'user_id': int(user),
            'score': round(v, 4)
        })
    metrics['top_pagerank'] = top_pr

    btw = nx.betweenness_centrality(G, weight='weight')
    bw_p = []
    for user, v in btw.items():
        bw_p.append((user, v))
    bw_p.sort(key=lambda p: p[1], reverse=True)
    top_btw = []
    for user, v in bw_p[:10]:
        top_btw.append({
            'user_id': int(user),
            'score': round(v, 4)
        })
    metrics['top_betweenness'] = top_btw

    articulation_points = list(nx.articulation_points(undirected_G))
    ap_list = []
    for x in articulation_points:
        ap_list.append(int(x))
    metrics['articulation_points'] = ap_list

    bridges = list(nx.bridges(undirected_G))
    bridge_pairs = []
    for u, v in bridges:
        bridge_pairs.append((int(u), int(v)))
    metrics['bridges'] = bridge_pairs

    return metrics
