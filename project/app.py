import streamlit as st
import uuid
from authorization import authorization
from backend.tg_client import create_client
from backend.telethon_runner import TelethonRunner
from backend.tg_fetch_message import get_groups
from backend.graph_builder import build_graph
from pyvis.network import Network
import plotly.express as px
import pandas as pd
from telethon import TelegramClient
from backend.tg_get_statistic import get_statistic
from wordcloud import WordCloud
import matplotlib.pyplot as plt

from backend.tg_profile_stat import get_my_profile


def chat_stats(runner : TelethonRunner, client : TelegramClient) -> None:
    """
    Отображает страницу статистики чата в приложении Streamlit.

    Функция предоставляет интерфейс для:
        1. Выбора группы (чата) из списка диалогов пользователя.
        2. Установки лимита сообщений для анализа (от 500 до 5000).
        3. Расчёта и отображения следующих метрик:
            - Топ‑10 самых активных участников (таблица с количеством сообщений и долей).
            - Почасовая активность (столбчатая диаграмма).
            - Облако самых частых слов.
            - Облако самых частых фраз (из 2–5 слов).
    Возвращает:
        None. Функция непосредственно рендерит элементы интерфейса в Streamlit.
    """
    st.title("Статистика по чатам")

    if "group_options" not in st.session_state:
        groups = runner.run(get_groups(client))
        st.session_state.group_options = {g["name"]: g["id"] for g in groups}

    group_names = list(st.session_state.group_options.keys())
    if "selected_group_name" not in st.session_state:
        st.session_state.selected_group_name = group_names[0]
    if "message_limit" not in st.session_state:
        st.session_state.message_limit = 1000

    selected_group_id = st.selectbox("Выберите группу",
                                     group_names,
                                     key="selected_group_name")

    limit = st.number_input("Введите количество сообщений на основе, которых строится граф",
                            min_value=500,
                            max_value=5000,
                            value=st.session_state.message_limit,
                            step=100,
                            key="message_limit")

    st.caption('Не рекомендуется ставить больше 1500')
    st.subheader("Статистика по чату")
    if "statistics" not in st.session_state:
        st.session_state.statistics = runner.run(get_statistic(client, selected_group_id, limit))

    top10_messages = st.session_state.statistics["top10_messages"]
    table = pd.DataFrame([{"Участник" : row["full_name"],
                           "Количество Сообщений" : row["count"],
                           "Процент от общего количество" : row["percent"]} for row in top10_messages])
    st.dataframe(table, use_container_width=True)

    hourly_activity = st.session_state.statistics['hourly_activity']
    df = pd.DataFrame([{"Часы" : hour, "Количество сообщений" :  hourly_activity.get(hour, 0)} for hour in range(24)])
    st.bar_chart(df,
                 x="Часы",
                 y="Количество сообщений",
                 color="#1f77b4",
                 horizontal=False)

    st.subheader("Облако самых частых слов")
    top_words_data = st.session_state.statistics['top_words']
    freq = {item['word']: item['count'] for item in top_words_data}
    wc = WordCloud(width=800, height=400, background_color='white', colormap='viridis').generate_from_frequencies(
        freq)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

    st.subheader("Облако самых частых фраз")
    top_phrases = st.session_state.statistics['top_phrases']
    freq = {item['phrase']: item['count'] for item in top_phrases}
    wc = WordCloud(width=800, height=400, background_color='white', colormap='viridis').generate_from_frequencies(
        freq)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)



def profile(runner : TelethonRunner, client : TelegramClient) -> None:
    """
    Отображает страницу личного профиля текущего авторизованного пользователя.

    Функция загружает и показывает:
        - Аватар пользователя (изображение).
        - Имя и фамилию.
        - Username (никнейм).
        - Номер телефона.
        - Биографию («о себе»).
        - Текущий статус (онлайн/офлайн).

    Данные профиля кэшируются в `st.session_state.profile_info`, чтобы избежать
    повторных запросов к Telegram API при перерисовке страницы (например, при
    взаимодействии с другими виджетами).

    Возвращает:
        None. Функция непосредственно рендерит элементы интерфейса в Streamlit.
    """
    st.title("Личный рофиль")
    if "profile_info" not in st.session_state:
        st.session_state.profile_info = runner.run(get_my_profile(client))
    first_name = st.session_state.profile_info['first_name']
    last_name = st.session_state.profile_info["last_name"]
    username = st.session_state.profile_info["username"]
    user_phone = st.session_state.profile_info["phone"]
    bio = st.session_state.profile_info["bio"]
    avatar_path = st.session_state.profile_info["avatar_path"]
    status = st.session_state.profile_info["status"]

    col1, col2 = st.columns(2)

    with col1:
        st.image(avatar_path)

    with col2:
        st.subheader(f"{first_name} {last_name}")
        st.caption(f"username: {username}")
        st.caption(f"phone: {user_phone}")
        if bio:
            st.text(f"Личная информация: {bio}")
        if (status == "UserStatusOnline"):
            st.text(f"status: online")
        else:
            st.text(f"status: offline")



def graph_vizualization(runner : TelethonRunner, client : TelegramClient) -> None:
    """
    Отображает страницу «Граф отношений» в приложении Streamlit.

    Функция предоставляет интерфейс для:
        1. Выбора группы (чата) из списка диалогов пользователя.
        2. Установки лимита сообщений для анализа (от 500 до 5000).
        3. Построения ориентированного графа взаимодействий между участниками чата.
        4. Визуализации графа с помощью библиотеки pyvis (интерактивный граф).
        5. Вывода статистики графа: количество узлов/рёбер, плотность, доля в главном ядре,
           сообщества (алгоритм Лувена), топ центральности (Degree, PageRank, Betweenness),
           точки сочленения, мосты.

    Использует `st.session_state` для кэширования:
        - group_options : dict – сопоставление названий групп с их ID.
        - selected_group_name : str – текущая выбранная группа (для сохранения между переходами).
        - message_limit : int – лимит сообщений (сохраняется в session_state).
        - graph_data : dict или None – результат построения графа (nodes, edges, metrics, users).

    Параметры (получаемые из внешнего окружения):
        - runner : TelethonRunner – объект для синхронного запуска асинхронных функций.
        - client : TelegramClient – авторизованный клиент Telegram (доступен как runner.client).

    Returns:
        None. Функция непосредственно рендерит элементы интерфейса и визуализации в Streamlit.
    """
    st.title("Граф общения")

    if "group_options" not in st.session_state:
        groups = runner.run(get_groups(client))
        st.session_state.group_options = {g["name"]: g["id"] for g in groups}

    group_names = list(st.session_state.group_options.keys())
    if "selected_group_name" not in st.session_state:
        st.session_state.selected_group_name = group_names[0] if group_names else None
    if "message_limit" not in st.session_state:
        st.session_state.message_limit = 1000
    if "graph_data" not in st.session_state:
        st.session_state.graph_data = None

    selected_group_name = st.selectbox(
        "Выберите группу",
        group_names,
        key="selected_group_name"
    )
    selected_group_id = st.session_state.group_options[selected_group_name]

    limit = st.number_input(
        "Введите количество сообщений для построения графа",
        min_value=500,
        max_value=5000,
        value=st.session_state.message_limit,
        step=100,
        key="message_limit"
    )
    st.caption("Не рекомендуется ставить больше 1500 (может быть долго).")

    if st.button("Построить граф"):
        with st.spinner("Подождите, идёт построение графа..."):
            graph = runner.run(build_graph(client, selected_group_id, int(limit)))
            st.session_state.graph_data = graph

    if st.session_state.graph_data is not None:
        graph = st.session_state.graph_data
        nodes = graph["nodes"]
        edges = graph["edges"]
        metrics = graph["metrics"]
        users_dict = graph["users"]

        st.subheader("Визуализация взаимодействий")
        net = Network(height="700px", width="100%", directed=True, notebook=False)
        for node in nodes:
            net.add_node(node["id"], node["full_name"], node["username"])
        for edge in edges:
            title = f"Ответов: {edge['replied']}, Упоминаний: {edge['mentioned']}, Быстрых ответов: {edge['rapid_answer']}"
            net.add_edge(edge["sender"], edge["target"], value=edge["weight"], title=title)

        net.set_options(
            """{
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -3000,
                    "centralGravity": 0.3,
                    "springLength": 150
                },
                "minVelocity": 0.75
            }
        }"""
        )
        html = net.generate_html()
        st.components.v1.html(html, height=750, scrolling=True)

        st.subheader("Статистика социального графа")

        col1, col2, col3 = st.columns(3)
        col1.metric("Участников", metrics.get("nodes_count", 0))
        col2.metric("Связей (рёбер)", metrics.get("edges_count", 0))
        col3.metric("Плотность", f"{metrics.get('density', 0):.4f}")

        if metrics.get("edges_count", 0) > 0:
            giant = metrics.get("giant_component_ratio", 0)
            st.metric("Доля участников в главном ядре", f"{giant:.1%}")

            communities = metrics.get("communities", [])
            with st.expander("Сообщества (алгоритм Лувена)"):
                for comm in communities[:5]:
                    member_names = []
                    for uid in comm["members"][:10]:
                        name = users_dict.get(uid, {}).get("full_name", f"id{uid}")
                        member_names.append(name)
                    members_preview = ", ".join(member_names)
                    st.write(f"Сообщество {comm['community_id']} – {comm['size']} участников: {members_preview}")

            def get_name(uid):
                return users_dict.get(uid, {}).get("full_name", f"id{uid}")

            top_central = metrics.get("top_central_users", [])
            if top_central:
                st.write("Самые центральные участники (Degree Centrality)")
                df_cent = pd.DataFrame([
                    {"Участник": get_name(item["user_id"]), "Центральность": item["centrality"]}
                    for item in top_central
                ])
                st.dataframe(df_cent, use_container_width=True)

            top_pr = metrics.get("top_pagerank", [])
            if top_pr:
                st.write("Самые авторитетные участники (PageRank)")
                df_pr = pd.DataFrame([
                    {"Участник": get_name(item["user_id"]), "PageRank": item["score"]}
                    for item in top_pr
                ])
                st.dataframe(df_pr, use_container_width=True)

            top_btw = metrics.get("top_betweenness", [])
            if top_btw:
                st.write("Главные связующие звенья (Betweenness Centrality)")
                df_btw = pd.DataFrame([
                    {"Участник": get_name(item["user_id"]), "Betweenness": item["score"]}
                    for item in top_btw
                ])
                st.dataframe(df_btw, use_container_width=True)

            articulation = metrics.get("articulation_points", [])
            if articulation:
                art_names = [get_name(uid) for uid in articulation[:20]]
                st.write("Точки сочленения (при удалении которых граф распадается)")
                st.write(", ".join(art_names))
                if len(articulation) > 20:
                    st.write(f"... и ещё {len(articulation) - 20}")

            bridges = metrics.get("bridges", [])
            if bridges:
                bridge_str = []
                for u, v in bridges[:20]:
                    name_u = get_name(u)
                    name_v = get_name(v)
                    bridge_str.append(f"{name_u} {name_v}")
                st.write("(связи, разрывающие граф)")
                st.write(", ".join(bridge_str))
                if len(bridges) > 20:
                    st.write(f"... и ещё {len(bridges) - 20}")

        else:
            st.warning("Граф не содержит рёбер (в выбранном диапазоне нет взаимодействий).")
    else:
        st.info("Нажмите «Построить граф», чтобы отобразить визуализацию и статистику.")

def main():
    if "session_name" not in st.session_state:
        st.session_state.session_name = f"session_{uuid.uuid4().hex[:8]}"

    if "runner" not in st.session_state:
        client = create_client(st.session_state.session_name)
        st.session_state.runner = TelethonRunner(client)

    runner = st.session_state.runner
    client = runner.client

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        authorization(runner)
        st.stop()

    pages = {
        "Граф общения": "graph_vizualization",
        "Статистика общения": "chat_stats",
        "Личный кабинет": "profile",
    }

    with st.sidebar:
        st.title("Меню")
        selected_page = st.radio(
            "Выберите раздел",
            list(pages.keys()),
            key="current_page"
        )

        st.divider()
        if st.button("Выйти"):
            runner.stop()
            for key in list(st.session_state.keys()):
                if key not in ("current_page",):
                    del st.session_state[key]
            st.rerun()

    page_id = pages[st.session_state.current_page]
    page_show = {
        "chat_stats": chat_stats,
        "profile": profile,
        "graph_vizualization": graph_vizualization,
    }

    page_func = page_show.get(page_id)
    if page_func:
        page_func(runner, client)

if __name__ == '__main__':
    main()
