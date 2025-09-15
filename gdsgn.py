import os
import csv
import asyncio
from datetime import datetime

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
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

from aiogram.client.session.aiohttp import AiohttpSession
session = AiohttpSession()
session._connector_init = {'ssl': False}

bot = Bot(token=secrets['BOT_API_TOKEN'], session=session)
dp = Dispatcher()


# Кнопки
start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Старт")]
    ],
    resize_keyboard=True
)

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Случайная собака")],
        [KeyboardButton(text="Факт о котах")],
        [KeyboardButton(text="Случайный пользователь")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)


@dp.message(lambda m: m.text == "/start")
async def cmd_start(message: types.Message):
    log_function(message.from_user, motion="Keyboard typing", api="NONE", api_answer="NONE")
    await message.answer(
        "Добро пожаловать! Нажмите кнопку «Старт», чтобы открыть меню API-запросов:",
        reply_markup=start_kb
    )

@dp.message(lambda m: m.text == "Старт")
async def on_start_button(message: types.Message):
    log_function(message.from_user, motion="Button press", api="start", api_answer="")
    await message.answer(
        "Выберите один из трёх API-запросов:",
        reply_markup=menu_kb
    )

@dp.message(lambda m: m.text == "Случайная собака")
async def random_dog(message: types.Message):
    log_function(message.from_user, motion="Button press", api="dog", api_answer="")
    url = "https://dog.ceo/api/breeds/image/random"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get("message"):
                dog_url = data["message"]
                log_function(message.from_user, motion="API", api="dog", api_answer=dog_url)
                await message.answer_photo(dog_url, caption="Случайная собака")
            else:
                error_text = f"Ошибка при получении изображения (HTTP {resp.status})"
                log_function(message.from_user, motion="API", api="dog", api_answer=error_text)
                await message.answer(error_text)

@dp.message(lambda m: m.text == "Факт о котах")
async def send_cat_fact(message: types.Message):
    log_function(message.from_user, motion="Button press", api="catfact", api_answer="")
    url = "https://catfact.ninja/fact"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get("fact"):
                fact = data["fact"]
                log_function(message.from_user, motion="API", api="catfact", api_answer=fact)
                await message.answer(f"Факт о котах:\n{fact}")
            else:
                error_text = "Не удалось получить факт о котах."
                log_function(message.from_user, motion="API", api="catfact", api_answer=error_text)
                await message.answer(error_text)

@dp.message(lambda m: m.text == "Случайный пользователь")
async def send_random_user(message: types.Message):
    log_function(message.from_user, motion="Button press", api="random user", api_answer="")
    url = "https://randomuser.me/api/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get("results"):
                u = data["results"][0]
                full_name = f"{u['name']['title']} {u['name']['first']} {u['name']['last']}"
                email = u.get("email", "неизвестно")
                country = u.get("location", {}).get("country", "неизвестно")
                text = (
                    "Случайный пользователь:\n"
                    f"Имя: {full_name}\n"
                    f"Email: {email}\n"
                    f"Страна: {country}"
                )
                log_function(message.from_user, motion="API", api="random user", api_answer=text)
                await message.answer(text)
            else:
                error_text = f"Ошибка при получении случайного пользователя (HTTP {resp.status})"
                log_function(message.from_user, motion="API", api="random user", api_answer=error_text)
                await message.answer(error_text)

@dp.message(lambda m: m.text == "Назад")
async def go_back(message: types.Message):
    log_function(message.from_user, motion="Button press", api="back", api_answer="")
    await message.answer("Главное меню:", reply_markup=start_kb)

@dp.message()
async def unknown_message_handler(message: types.Message):
    log_function(message.from_user, motion="Keyboard typing", api="NONE", api_answer="NONE")
    await message.reply(f'Вы написали "{message.text}", я не знаю такой команды')

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
