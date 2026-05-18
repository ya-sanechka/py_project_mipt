import streamlit as st
import uuid
from authorization import authorization
from backend.tg_client import create_client
from backend.telethon_runner import TelethonRunner
from backend.tg_fetch_message import get_groups
from backend.graph_builder import build_graph
from pyvis.network import Network

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

def chat_stats():
    st.title("Статистика по чатам")

    if "group_options" not in st.session_state:
        groups = runner.run(get_groups(client))
        st.session_state.group_options = {g["name"]: g["id"] for g in groups}

    group_names = list(st.session_state.group_options.keys())
    if "selected_group_name" not in st.session_state:
        st.session_state.selected_group_name = group_names[0]

    selected_group_id = st.selectbox("Выберите группу",
                                     group_names,
                                     key="selected_group_name")

def profile():
    pass

def graph_vizualization():
    """
    Отображает страницу «Граф отношений» в приложении Streamlit.

    Функция позволяет пользователю выбрать группу (чат) из списка, задать количество
    сообщений для анализа, построить ориентированный граф взаимодействий между участниками
    и визуализировать его с помощью библиотеки pyvis.

    Работа функции полностью основана на `st.session_state` для сохранения состояния
    между переключениями страниц и перезапусками скрипта:
        - `group_options` : dict — сопоставление названий групп с их идентификаторами.
        - `selected_group_name` : str — название текущей выбранной группы.
        - `message_limit` : int — количество последних сообщений, используемых для построения графа.
        - `graph_data` : dict или None — результат работы `build_graph` (узлы, рёбра, метрики).

    Алгоритм работы:
        1. При первом вызове (или если данные групп отсутствуют) загружает список групп через `get_groups`
           и сохраняет его в `st.session_state.group_options`.
        2. Инициализирует недостающие ключи `selected_group_name`, `message_limit`, `graph_data`
           значениями по умолчанию.
        3. При нажатии кнопки вызывает `build_graph` с выбранным ID группы и лимитом,
           сохраняет результат в `st.session_state.graph_data`.
        4. Если `graph_data` не `None`:
            - создаёт интерактивный граф через `pyvis.Network`,
            - добавляет узлы (участники) и рёбра (взаимодействия) с весами и подписями,
        5. Иначе выводит информационное сообщение.

    Returns:
        None. Функция непосредственно рендерит интерфейс и график в Streamlit.
    """

    st.title("Граф общения")

    if "group_options" not in st.session_state:
        groups = runner.run(get_groups(client))
        st.session_state.group_options = {g["name"]: g["id"] for g in groups}

    group_names = list(st.session_state.group_options.keys())
    if "selected_group_name" not in st.session_state:
        st.session_state.selected_group_name = group_names[0]
    if "message_limit" not in st.session_state:
        st.session_state.message_limit = 1000
    if "graph_data" not in st.session_state:
        st.session_state.graph_data = None

    selected_group_id = st.selectbox("Выберите группу",
                                     group_names,
                                     key="selected_group_name")

    limit = st.number_input("Введите количество сообщений на основе, которых строится граф",
                          min_value = 500,
                          max_value = 5000,
                          value = st.session_state.message_limit,
                          step = 100,
                          key = "message_limit")

    st.caption('Не рекомендуется ставить больше 1500')
    if st.button("Построить граф"):
        with st.spinner("Подождите, идет построение графа"):
            graph = runner.run(build_graph(client, selected_group_id, int(limit)))
            st.session_state.graph_data = graph

    if st.session_state.graph_data is not None:
        graph = st.session_state.graph_data
        nodes = graph["nodes"]
        edges = graph["edges"]

        net = Network(height="700px", width="700px", directed=True, notebook=False)
        for node in nodes:
            net.add_node(node["id"], node["full_name"], node["username"])
        for edge in edges:
            title = f"Ответов: {edge['replied']}, Упоминаний: {edge['mentioned']}"
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
        st.components.v1.html(html, height=750, width=750, scrolling=True)
    else:
        st.info("Нажмите «Построить граф», чтобы отобразить визуализацию.")





page_id = pages[st.session_state.current_page]
page_show = {
    "chat_stats": chat_stats,
    "profile": profile,
    "graph_vizualization": graph_vizualization,
}

page_func = page_show.get(page_id)
if page_func:
    page_func()