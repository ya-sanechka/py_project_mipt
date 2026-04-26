import streamlit as st
from authorization import authorization

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    authorization()
    st.stop()

st.title("empty title")

