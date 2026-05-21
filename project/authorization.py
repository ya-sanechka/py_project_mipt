import streamlit as st
from backend.tg_client import request_code, sign_in, create_client, send_password


def authorization(runner):
    """Функция предоставляет интерфейс для авторизации на сайт

    Аргументов функция не принимает, просто запускается процесс авторизации при вызове

    Фактически функция дает полностью готовый авторизациооный интерфейс, зашадшему открывается страница
    с строкой ввода телефона, в случае неправильного ввода, пользователь получает ошибку (об ошибках подробнее
    в документации в request_code, sign_in и enter_password, ибо ошибки берутся оттуда

    Далее пользователь получает код и в случае установленной двухфакторной аутентификации пользователь получает
    пароль, все некорректные вводы обрабатываются соответсвующими ошибками

    После успещного захода на сайт пользователю открывается основаная страничка сайта"""

    client = runner.client

    if "step" not in st.session_state:
        st.session_state.step = "phone"

    if st.session_state.step == "phone":
        st.title('Авторизация в telegram')
        phone_number = st.text_input('Введите свой номер телефона')
        st.session_state.phone = phone_number
        st.caption('Формат: +7XXXXXXXXXX, например +79001234567')

        if st.button('Продолжить'):
            if phone_number:
                phone_response = runner.run(request_code(client, phone_number))

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
        st.caption(f"Код отправлен на номер {st.session_state.phone}")
        st.session_state.code = telegram_code

        if st.button('Продолжить', key='continue_btn'):
            if telegram_code:
                code_response = runner.run(sign_in(
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

                elif code_response["status"] == "password_needed":
                    st.warning(code_response["message"])
                    st.session_state.step = "password"
                    st.rerun()

                else:
                    st.session_state.logged_in = True
                    st.session_state.step = "phone"
                    st.rerun()

        if st.button('Назад'):
            st.session_state.step = "phone"
            st.rerun()

    elif st.session_state.step == "password":
        st.title("Двухфакторная аутентификация")
        password = st.text_input("Введите пароль", type="password")
        st.session_state.password = password

        if st.button("Войти"):
            if password:
                password_response = runner.run(send_password(client, password))

                if password_response["status"] == "error":
                    if password_response["error_type"] == "invalid_password":
                        st.error(password_response["message"])
                    elif password_response["error_type"] == "flood_wait":
                        st.error(password_response["message"])
                else:
                    st.success(f"Добро пожаловать {password_response['user']}")
                    st.session_state.logged_in = True
                    st.session_state.step = "phone"
                    st.rerun()
            else:
                st.warning("Введите пароль")