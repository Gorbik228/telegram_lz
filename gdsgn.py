import os
import csv
import asyncio
from datetime import datetime

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from secret import secrets

# Путь к файлу лога
LOG_FILE = "user_logs.csv"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Unic_ID", "@TG_nick", "Motion", "API", "Date", "Time", "API_answer"
        ])

def log_function(user: types.User, motion: str, api: str, api_answer: str):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    username = f"@{user.username}" if user.username else ""
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            user.id, username, motion, api, date_str, time_str, api_answer
        ])

bot = Bot(token=secrets["BOT_API_TOKEN"])
dp = Dispatcher()

# Кнопка «Старт»
start_builder = InlineKeyboardBuilder()
start_builder.button(
    text="Нажмите Старт, чтобы открыть меню API-запросов",
    callback_data="start"
)
start_builder.adjust(1)
kb_start = start_builder.as_markup()

# Главное меню
menu_builder = InlineKeyboardBuilder()
menu_builder.button(text="Случайная собака", callback_data="dog")
menu_builder.button(text="Факт о котах", callback_data="catfact")
menu_builder.button(text="Случайный пользователь", callback_data="random user")
menu_builder.adjust(1, 1, 1)
kb_menu = menu_builder.as_markup()

@dp.message(lambda m: m.text == "/start")
async def cmd_start(message: types.Message):
    log_function(message.from_user, motion="Keyboard typing", api="NONE", api_answer="NONE")
    await message.answer(
        "Добро пожаловать! Нажмите кнопку ниже, чтобы продолжить:",
        reply_markup=kb_start
    )

@dp.callback_query(lambda c: c.data in {"start", "dog", "catfact", "random user"})
async def process_menu(call: types.CallbackQuery):
    log_function(call.from_user, motion="Button press", api=call.data, api_answer="")
    await call.answer()

    if call.data == "start":
        await call.message.edit_text(
            "Выберите один из трёх API-запросов:",
            reply_markup=kb_menu
        )
        return

    async with aiohttp.ClientSession() as session:
        if call.data == "dog":
            url = "https://dog.ceo/api/breeds/image/random"
            async with session.get(url) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("message"):
                    dog_url = data["message"]
                    log_function(call.from_user, motion="Button press", api="dog", api_answer=dog_url)
                    await call.message.edit_media(
                        media=InputMediaPhoto(media=dog_url, caption="Случайная собака"),
                        reply_markup=kb_menu
                    )
                    return
                text = f"Ошибка при получении изображения (HTTP {resp.status})"

        elif call.data == "catfact":
            url = "https://catfact.ninja/fact"
            async with session.get(url) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("fact"):
                    text = f"Факт о котах:\n{data['fact']}"
                else:
                    text = "Не удалось получить факт о котах."

        else:  # random user
            url = "https://randomuser.me/api/"
            async with session.get(url) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("results"):
                    user_info = data["results"][0]
                    name = user_info["name"]
                    full_name = f"{name['title']} {name['first']} {name['last']}"
                    email = user_info.get("email", "неизвестно")
                    country = user_info.get("location", {}).get("country", "неизвестно")
                    text = (
                        "Случайный пользователь:\n"
                        f"Имя: {full_name}\n"
                        f"Email: {email}\n"
                        f"Страна: {country}"
                    )
                else:
                    text = f"Ошибка при получении случайного пользователя (HTTP {resp.status})"

    log_function(call.from_user, motion="Button press", api=call.data, api_answer=text)
    await call.message.edit_text(text, reply_markup=kb_menu)

@dp.message()
async def unknown_message_handler(message: types.Message):
    log_function(message.from_user, motion="Keyboard typing", api="NONE", api_answer="NONE")
    await message.reply(f'Вы написали "{message.text}", я не знаю такой команды')

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
