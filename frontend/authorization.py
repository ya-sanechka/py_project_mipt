import streamlit as st
import phonenumbers
from phonenumbers import PhoneNumberFormat, NumberParseException
from phonenumbers.phonenumberutil import is_valid_number
import re

def valid_number_checker(phone_number : str) -> bool:
    try:
        parsed = phonenumbers.parse(phone_number, None)
        return phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed)
    except:
        return False

def valid_code_checker(telegram_code : str) -> bool:
    code_pattern = re.compile(r'^\d{4}$')
    if re.match(code_pattern, telegram_code):
        return True
    return False

def authorization():
    st.title('Авторизация в telegram')
    phone_number = st.text_input('Введите свой номер телефона')
    st.caption('Формат: +7XXXXXXXXXX, например +79001234567')
    if st.button('Продолжить'):
        if phone_number:
            if valid_number_checker(phone_number):
                st.success('Отправили код на ваш телеграмм аккаутнт')
                telegram_code = st.text_input('Введите отправленный вам телеграмм-код')
                if st.button('Продолжить', key='continue_btn'):
                    if telegram_code:
                        if valid_code_checker(telegram_code):
                            try:
                                st.session_state.logged_in = True
                                st.rerun()
                            except:
                                st.error('Неверный код')
                        else:
                            st.error('Некорректный формат')
                    else:
                        st.warning('Введите код')
            else:
                st.error('Такого номера телефона не сущесвует')
        else:
            st.warning('Введите номер телефона')

authorization()
