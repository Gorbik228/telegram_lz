import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from secret import secrets

bot = Bot(token=secrets["BOT_API_TOKEN"])
dp = Dispatcher()

# Кнопка «Старт»
start_builder = InlineKeyboardBuilder()
start_builder.button(text="Старт", callback_data="start")
start_builder.adjust(1)
kb_start = start_builder.as_markup()

# Главное меню: курс Bitcoin, факт о котах, данные World Bank
menu_builder = InlineKeyboardBuilder()
menu_builder.button(text="Курс Bitcoin",        callback_data="bitcoin")
menu_builder.button(text="Факт о котах",        callback_data="catfact")
menu_builder.button(text="Данные World Bank",   callback_data="wb")
menu_builder.adjust(1, 1, 1)
kb_menu = menu_builder.as_markup()


@dp.message(lambda m: m.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer(
        "Нажмите «Старт», чтобы открыть меню API-запросов:",
        reply_markup=kb_start
    )


@dp.callback_query(lambda c: c.data in {"start", "bitcoin", "catfact", "wb"})
async def process_menu(call: types.CallbackQuery):
    await call.answer()

    if call.data == "start":
        await call.message.edit_text(
            "Выберите один из трёх API-запросов:",
            reply_markup=kb_menu
        )
        return

    async with aiohttp.ClientSession() as session:
        if call.data == "bitcoin":
            url = "https://api.coindesk.com/v1/bpi/currentprice.json"
            async with session.get(url) as resp:
                data = await resp.json()
            if resp.status == 200 and data.get("bpi"):
                usd = data["bpi"]["USD"]["rate"]
                gbp = data["bpi"]["GBP"]["rate"]
                eur = data["bpi"]["EUR"]["rate"]
                text = (
                    "Текущая цена Bitcoin:\n"
                    f"USD: {usd}\n"
                    f"GBP: {gbp}\n"
                    f"EUR: {eur}"
                )
            else:
                text = f"Ошибка при получении курса Bitcoin (HTTP {resp.status})"

        elif call.data == "catfact":
            url = "https://catfact.ninja/fact"
            async with session.get(url) as resp:
                data = await resp.json()
            if resp.status == 200 and data.get("fact"):
                text = f"Факт о котах:\n{data['fact']}"
            else:
                text = "Не удалось получить факт о котах."

        else:  # World Bank
            url = (
                "https://search.worldbank.org/api/v3/wds"
                "?format=json&qterm=energy&display_title=water"
                "&fl=display_title&rows=2&os=20"
            )
            async with session.get(url) as resp:
                data = await resp.json()
            if resp.status == 200 and data.get("rows"):
                titles = [r["display_title"] for r in data["rows"]]
                text = "Результаты поиска World Bank:\n" + "\n".join(titles)
            else:
                text = "Ошибка при запросе к World Bank."

    await call.message.edit_text(text, reply_markup=kb_menu)


@dp.message()
async def unknown_message_handler(message: types.Message):
    await message.reply(
        f'Вы написали "{message.text}", я не знаю такой команды'
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
