import streamlit as st
from authorization import authorization
import asyncio
import nest_asyncio
nest_asyncio.apply()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    asyncio.run(authorization())
    st.stop()

st.title("empty title")

