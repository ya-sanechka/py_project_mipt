import streamlit as st
import phonenumbers
from phonenumbers import PhoneNumberFormat, NumberParseException
from phonenumbers.phonenumberutil import is_valid_number
from streamlit.web.server.oauth_authlib_routes import create_oauth_client

from backend.tg_client import request_code, sign_in, create_client
import re
import asyncio

# def valid_number_checker(phone_number : str) -> bool:
#     try:
#         parsed = phonenumbers.parse(phone_number, None)
#         return phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed)
#     except:
#         return False
#
# def valid_code_checker(telegram_code : str) -> bool:
#     code_pattern = re.compile(r'^\d{4}$')
#     if re.match(code_pattern, telegram_code):
#         return True
#     return False

async def authorization():
    if "step" not in st.session_state:
        st.session_state.step = "phone"
    if st.session_state.step == "phone":
        st.title('Авторизация в telegram')
        phone_number = st.text_input('Введите свой номер телефона')
        st.session_state.phone = phone_number
        st.caption('Формат: +7XXXXXXXXXX, например +79001234567')
        if st.button('Продолжить'):
            if phone_number:
                client = create_client()
                phone_response = asyncio.run(request_code(client, phone_number))
                if phone_response["status"] == "error":
                    if phone_response["error_type"] == "invalid_phone":
                        st.error(phone_response["message"])
                    elif phone_response["error_type"] == "flood_type":
                        st.error(phone_response["message"])
                elif phone_response["status"] == "code_sent":
                    st.session_state.phone = phone_number
                    st.session_state.phone_code_hash = phone_response["phone_code_hash"]
                    st.success(phone_response["message"])
                    st.session_state.step = "code"
                    st.rerun()
            else:
                st.warning('Введите номер телефона')
    elif st.session_state.step == "code":
        st.title("Получение кода")
        telegram_code = st.text_input('Введите отправленный вам телеграмм-код')
        st.session_state.code = telegram_code
        if st.button('Продолжить', key='continue_btn'):
            if telegram_code:
                client = create_client()
                code_response = asyncio.run(sign_in(
                    client,
                    st.session_state.phone,
                    telegram_code,
                    st.session_state.phone_code_hash
                ))
                if code_response["status"] == "error":
                    if code_response["error_type"] == "invalid_code":
                        st.error(code_response["message"])
                    elif code_response["error_type"] == "code_expired":
                        st.error(code_response["message"])
                    elif code_response["error_type"] == "flood_type":
                        st.error(code_response["message"])
                    # тут надо обработать последнюю ошибку с паролем (((
                else:
                    st.session_state.logged_in = True
                    st.session_state.step = "phone"
                    st.rerun()

