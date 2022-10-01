from enum import IntEnum, auto
import os

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

import shop_api

_database = None
_shop_host = ""
_shop_token = ""


class State(IntEnum):
    START = auto()
    HANDLE_MENU = auto()


def start(update: Update, _) -> State:
    products = shop_api.get_products(_shop_host, _shop_token)
    keyboard = [
        [
            InlineKeyboardButton(product["name"], callback_data=product["id"]),
        ] for product in products
    ]
    markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text='Привет!', reply_markup=markup)
    return State.HANDLE_MENU


def handle_menu(update: Update, _) -> State:
    query = update.callback_query
    query.answer()
    product_id = query.data
    product = shop_api.get_product(_shop_host, _shop_token, product_id)
    description = "\n".join(
        [
            product["name"],
            "\n",
            product["description"],
        ]
    )
    query.edit_message_text(text=description)
    return State.START


def handle_users_reply(update, context):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.

    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = State.START
    else:
        user_state = State(int(db.get(chat_id)))

    states_functions = {
        State.START: start,
        State.HANDLE_MENU: handle_menu,
    }
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, int(next_state))
    except Exception as err:
        print(err)


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        database_password = os.getenv("REDIS_PASSWORD")
        database_host = os.getenv("REDIS_HOST")
        database_port = os.getenv("REDIS_PORT")
        _database = redis.Redis(
            host=database_host, port=database_port, password=database_password)
    return _database


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    _shop_host = os.getenv("SHOP_HOST")
    client_id = os.getenv("SHOP_CLIENT_ID")
    _shop_token = shop_api.authenticate(_shop_host, client_id)

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
