import os
import sys

BASE_DIR = os.path.abspath('..')
sys.path.insert(0, os.path.join(BASE_DIR, 'project', 'backend'))
sys.path.insert(0, os.path.join(BASE_DIR, 'project'))

project = 'Анализ чатов Telegram'
copyright = '2026, Александра Спиридонова, Илья Захаров'
author = 'Александра Спиридонова, Илья Захаров'

extensions = [
    'sphinx.ext.autodoc',   # вставляет docstrings из кода
    'sphinx.ext.viewcode',  # добавляет ссылки на исходный код
    'sphinx_autodoc_typehints',     # собирает аннотации типов
]