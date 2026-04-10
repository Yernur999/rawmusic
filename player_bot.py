from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = "8791325141:AAEgU7utWIDV4t6VKzTALPiL3GQz1OXoptY"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("Бот работает. Напиши /play")

@dp.message_handler(commands=["play"])
async def play_music(message: types.Message):
    await bot.send_audio(
        chat_id=message.chat.id,
        audio="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        title="Test Track",
        performer="RawMusic"
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
