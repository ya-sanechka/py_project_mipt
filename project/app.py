import streamlit as st
from authorization import authorization
# from tg_fetch_message import get_groups
import asyncio
import nest_asyncio
from backend.tg_client import create_client
nest_asyncio.apply()
if "client" not in st.session_state:
    st.session_state.client = create_client()

client = st.session_state.client

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    asyncio.run(authorization())
    st.stop()

pages = {
    "Статистика по чатам": "chat_stats",
    "Личный кабинет": "profile",
    "Интерактивный анализ чата": "chat_analysis"
}

if "current_page" not in st.session_state:
    st.session_state.current_page = list(pages.keys())[0]

with st.sidebar:
    st.title("Меню")

    selected_page = st.radio(
        "Выберите раздел",
        list(pages.keys()),
        index=list(pages.keys()).index(st.session_state.current_page)
    )

    st.session_state.current_page = selected_page

    st.divider()

    if st.button("Выйти"):
        st.session_state.logged_in = False
        st.session_state.step = "phone"
        st.rerun()

st.title(st.session_state.current_page)

st.info("Здесь пока ничего нет 👀")
