import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db

BOT_TOKEN = "ضع_هنا_توكن_البوت"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    ref_id = None
    if msg.get_args().startswith("ref"):
        try:
            ref_id = int(msg.get_args().replace("ref", ""))
        except:
            pass

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="🚀 ابدأ اللعب",
            web_app=WebAppInfo(url=f"https://your-domain.com/?ref={ref_id}" if ref_id else "https://your-domain.com/")
        )
    )
    await msg.answer("مرحبًا بك في TAPNOVA!", reply_markup=kb)

async def main():
    init_db()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
