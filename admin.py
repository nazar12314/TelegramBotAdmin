from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters
from telegram.ext import ApplicationBuilder, ContextTypes, ChatMemberHandler

import telegram.error
import pandas as pd

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from config import *
from admin_constants import *


import textwrap
import io
import datetime
import os


TOKEN = os.getenv('BOTAPIKEY')
MONGO_URI = os.getenv('MONGOURI')


client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client[DB]


user_collection = db[USER_COLLECTION]
deleted_user_collection = db[DELETED_USER_COLLECTION]
advert_collection = db[ADVERT_COLLECTION]


admin_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Количество пользователей"), KeyboardButton("Выписка по пользователям")],
        [KeyboardButton("Количество отписанных"), KeyboardButton("Выписка по отписанным")],
        [KeyboardButton("Сделать объявление")],
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Выберите опцию", reply_markup=admin_keyboard)

    return States.ADMIN_PANEL.value


async def get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_count = user_collection.count_documents({})

    text_message = textwrap.dedent(
        f"""
        Количество пользователей: {user_count}
        """)

    await update.message.reply_text(text_message, reply_markup=admin_keyboard)

    return States.ADMIN_PANEL.value


async def get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_count = user_collection.count_documents({})

    text_message = textwrap.dedent(
        f"""
        Количество пользователей: {user_count}
        """)

    await update.message.reply_text(text_message, reply_markup=admin_keyboard)

    return States.ADMIN_PANEL.value


async def get_users_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    users_data_cursor = user_collection.find({})

    selected_fields = ['first_name', 'last_name', 'user_id', 'username']
    users_data_list = [{field: user.get(field) for field in selected_fields} for user in users_data_cursor]
    
    users_data_df = pd.DataFrame(users_data_list)

    csv_data = io.StringIO()
    users_data_df.to_csv(csv_data, index=False)

    csv_data.seek(0)
    await update.message.reply_document(document=csv_data, filename='users_data.csv', reply_markup=admin_keyboard)

    return States.ADMIN_PANEL.value


async def get_left_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_count = deleted_user_collection.count_documents({})

    text_message = textwrap.dedent(
        f"""
        Количество отписанных пользователей: {user_count}
        """)

    await update.message.reply_text(text_message, reply_markup=admin_keyboard)

    return States.ADMIN_PANEL.value


async def get_left_users_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    users_data_cursor = deleted_user_collection.find({})

    selected_fields = ['first_name', 'last_name', 'user_id', 'username']
    users_data_list = [{field: user.get(field) for field in selected_fields} for user in users_data_cursor]
    
    users_data_df = pd.DataFrame(users_data_list)

    csv_data = io.StringIO()
    users_data_df.to_csv(csv_data, index=False)
    
    csv_data.seek(0)
    await update.message.reply_document(document=csv_data, filename='left_users_data.csv', reply_markup=admin_keyboard)

    return States.ADMIN_PANEL.value


async def send_advert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите текст объявления:")

    return States.ADVERT_TEXT.value


async def get_advert_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_time = datetime.datetime.utcnow()

    advert_collection.delete_many({})
    advert_collection.insert_one({'text': update.message.text, 'creation_time': current_time})

    context.user_data.clear()

    # keyboard = ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True, resize_keyboard=True)
    # await update.message.reply_text("Хотите добавить изображение к объявлению?", reply_markup=keyboard)

    await update.message.reply_text("Объявления отправлено", reply_markup=admin_keyboard)

    return States.ADMIN_PANEL.value


# async def get_advert_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     await update.message.reply_text("Отправьте изображение для объявления:")

#     return States.ADVERT_IMAGE.value


# async def save_advert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     advert_text = context.user_data.get("advert_text")

#     advert_collection.insert_one({'text': advert_text})

#     context.user_data.clear()

#     return States.ADMIN_PANEL.value


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            States.ADMIN_PANEL.value: [
                MessageHandler(filters.Text("Количество пользователей"), get_users),
                MessageHandler(filters.Text("Количество отписанных"), get_left_users),
                MessageHandler(filters.Text("Выписка по пользователям"), get_users_data),
                MessageHandler(filters.Text("Выписка по отписанным"), get_left_users_data),
                MessageHandler(filters.Text("Сделать объявление"), send_advert),

            ],
            States.ADVERT_TEXT.value: [
                MessageHandler(filters.TEXT, get_advert_text),
            ],
            # States.ADVERT_IMAGE.value: [
            #     MessageHandler(filters.Text("Да"), get_advert_image),
            #     MessageHandler(filters.Text("Нет") | filters.PHOTO, save_advert),
            # ]
        },
        fallbacks=[],
    )

    app.add_handler(conversation_handler)

    # app.add_handler(CommandHandler("stop", stop))

    app.run_polling()


if __name__ == "__main__":
    main()
