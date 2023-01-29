import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ContentType

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = '5302213137:AAF3FOkvfBrak7C6LfN5dvNk-burSK4XXdA' 

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

async def set_main_menu(dp: Dispatcher):
    
    main_menu_commands = [
        types.BotCommand(command='/start', description='начало работы')
    ]
    await dp.bot.set_my_commands(main_menu_commands)

class Dialog(StatesGroup):
    content_photo = State()
    style_photo = State()
    processing = State()

if __name__ == '__main__':
    from handlers import dp
    executor.start_polling(dp, skip_updates=True)