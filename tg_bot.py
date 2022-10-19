import os
from enum import IntEnum, auto
from textwrap import dedent

import redis
from dotenv import load_dotenv
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      Update)
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

import shop_api

_database = None


class State(IntEnum):
    START = auto()
    MENU = auto()
    DESCRIPTION = auto()
    CART = auto()
    WAITING_EMAIL = auto()


def show_menu(message: Message) -> None:
    products = shop_api.get_products()
    keyboard = [
        [
            InlineKeyboardButton(product["name"], callback_data=product["id"]),
        ] for product in products
    ]
    keyboard.append([InlineKeyboardButton("Корзина", callback_data="cart")])
    markup = InlineKeyboardMarkup(keyboard)
    message.reply_text(text="Выберите товар:", reply_markup=markup)


def show_product(message: Message, product_id: str) -> None:
    product = shop_api.get_product(product_id)
    product_photo_url = shop_api.get_product_image_url(product_id)
    keyboard = [
        [
            InlineKeyboardButton("1 кг", callback_data=f"{product_id},1"),
            InlineKeyboardButton("5 кг", callback_data=f"{product_id},5"),
            InlineKeyboardButton("10 кг", callback_data=f"{product_id},10"),
        ],
        [
            InlineKeyboardButton("Корзина", callback_data="cart")
        ],
        [
            InlineKeyboardButton("Назад", callback_data="back"),
        ],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    description = f"""\
        {product["name"]}

        {product["meta"]["display_price"]["with_tax"]["formatted"]}

        {product["description"]}
    """

    message.reply_photo(
        product_photo_url, caption=dedent(description), reply_markup=markup)


def show_cart(message: Message, cart_reference: str) -> None:
    cart_description = shop_api.get_cart_items(cart_reference)
    total = cart_description["meta"]["display_price"]["with_tax"]["formatted"]
    cart_items = []
    keyboard = []
    for item in cart_description["data"]:
        cost = item["meta"]["display_price"]["with_tax"]
        item_description = f"""\
            {item["name"]}
            {cost['unit']['formatted']} за кг
            {item['quantity']} кг на сумму {cost['value']['formatted']}
        """
        cart_items.append(dedent(item_description))
        keyboard.append([InlineKeyboardButton(
            f"Убрать {item['name']}", callback_data=item["id"])])
    cart_items.append(f"Итого: {total}")
    cart_text = "\n".join(cart_items)
    keyboard.append([InlineKeyboardButton("В меню", callback_data="back")])
    keyboard.append([InlineKeyboardButton(
        "Оплатить", callback_data="checkout")])
    markup = InlineKeyboardMarkup(keyboard)
    message.reply_text(cart_text, reply_markup=markup)


def start(update: Update, _) -> State:
    shop_api.get_cart(cart_reference=update.effective_user.id)
    show_menu(update.message)
    return State.MENU


def handle_menu(update: Update, _) -> State:
    query = update.callback_query
    query.answer()
    query.delete_message()
    if query.data == "cart":
        show_cart(query.message, update.effective_user.id)
        return State.CART
    show_product(query.message, product_id=query.data)
    return State.DESCRIPTION


def handle_description(update: Update, _) -> State:
    query = update.callback_query
    query.answer()
    if query.data == "back":
        query.delete_message()
        show_menu(query.message)
        return State.MENU
    if query.data == "cart":
        query.delete_message()
        show_cart(query.message, update.effective_user.id)
        return State.CART
    product_id, quantity = query.data.split(",")
    shop_api.add_product_to_cart(
        cart_reference=update.effective_user.id,
        product_id=product_id,
        quantity=int(quantity)
    )
    return State.DESCRIPTION


def handle_cart(update: Update, _) -> State:
    query = update.callback_query
    query.answer()
    if query.data == "back":
        query.delete_message()
        show_menu(query.message)
        return State.MENU
    if query.data == "checkout":
        query.message.reply_text("Пожалуйста, укажите Ваш Email")
        return State.WAITING_EMAIL
    shop_api.remove_cart_item(
        cart_reference=update.effective_user.id,
        item_id=query.data,
    )
    query.delete_message()
    show_cart(query.message, cart_reference=update.effective_user.id)
    return State.CART


def input_email(update: Update, _) -> State:
    user_email = update.message.text
    user_name = update.effective_user.full_name
    response = shop_api.create_customer(name=user_name, email=user_email)
    customer_id = response['data']['id']
    print(customer_id)
    show_menu(update.message)
    return State.MENU


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
    if user_reply == "/start":
        user_state = State.START
    else:
        user_state = State(int(db.get(chat_id)))

    states_functions = {
        State.START: start,
        State.MENU: handle_menu,
        State.DESCRIPTION: handle_description,
        State.CART: handle_cart,
        State.WAITING_EMAIL: input_email,
    }
    state_handler = states_functions[user_state]
    next_state = state_handler(update, context)
    db.set(chat_id, int(next_state))


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


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    client_id = os.getenv("SHOP_CLIENT_ID")
    shop_api.authenticate(client_id)

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))
    updater.start_polling()
