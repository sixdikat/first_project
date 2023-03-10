from main import dp
import aiogram.types as types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher
import asyncio
import logging
from io import BytesIO

from NeuralTransfer.model import StyleTransformer

kb = types.InlineKeyboardMarkup(row_width=2)
kb.row(types.InlineKeyboardButton(text='Ок', callback_data='yes'),
       types.InlineKeyboardButton(text='Поменять фото', callback_data='change'))

class Dialog(StatesGroup):
    content_photo = State()
    style_photo = State()
    processing = State()


@dp.message_handler(commands=['start'])       
async def welcome(msg: types.Message):
    greeting = "Привет. Это бот для стилизации изображений.\n" \
               "Отправь фото, ***на которое ты хочешь перенести стиль***."

    await Dialog.content_photo.set()
    await msg.answer(greeting, parse_mode='markdown')


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
     print('cancel')
     current_state = await state.get_state()
     if current_state is None:
        return

     logging.info('Cancelling state %r', current_state)

     await state.reset_data()
     await Dialog.content_photo.set()

     await message.reply('Начнём заново.\n'
                         'Отправьте фото, на которое хотите стиль',
                         reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Dialog.content_photo, content_types=ContentType.all())
async def get_photo(msg: types.Message, state: FSMContext):
    print('get_content')

    if msg.content_type != 'photo':
        await msg.reply('Нужно фото')
        return

    await msg.reply('Получил фото.\nТеперь отправьте фото ***со стилем***',
                    parse_mode='markdown')
    photo = msg.photo[-1]
    await state.update_data(content=photo)
    await msg.answer('Подтверждаете фото?', reply_markup=kb)


@dp.message_handler(state=Dialog.style_photo, content_types=ContentType.all())
async def get_style_photo(msg: types.Message, state: FSMContext):
    if msg.content_type != 'photo':
        await msg.reply('Нужно фото')
        return

    await msg.reply('Получил оба фото')
    photo = msg.photo[-1]
    await state.update_data(style=photo)
    await msg.answer('Начать перенос?', reply_markup=kb)


@dp.callback_query_handler(text='yes', state=Dialog.style_photo)
async def process(call: types.CallbackQuery, state: FSMContext):
    await Dialog.processing.set()
    await call.message.answer('Начинаю перенос. Придётся подождать несколько минут')
    await call.answer()
    async with state.proxy() as data:
        content = BytesIO()
        await data['content'].download(destination_file=content)
        style = BytesIO()
        await data['style'].download(destination_file=style)
        content.seek(0)
        style.seek(0)

        loop = asyncio.get_event_loop()
        net = await loop.run_in_executor(None, StyleTransformer)
        img = await loop.run_in_executor(None, net.transfer, content, style)

        bio = BytesIO()
        bio.name = 'image.jpeg'
        img.save(bio, 'JPEG')
        bio.seek(0)

    await call.message.answer_photo(bio, caption='Done!\n'
                                                 'Для продолжения используйте команду /start.')
    await state.finish()
    print('Finished', await state.get_state())


@dp.callback_query_handler(text='yes', state=Dialog.content_photo)
async def process(call: types.CallbackQuery):
    await Dialog.style_photo.set()
    await call.message.answer('Отлично\nТеперь отправьте фото ***со стилем***.',
                              parse_mode='markdown')
    await call.answer()


@dp.callback_query_handler(text='change', state=Dialog.content_photo)
async def change_photo(call: types.CallbackQuery):
    await call.message.answer('Пришли новое фото, ***на которое хочешь перенести стиль***',
                              parse_mode='markdown')
    await call.answer()


@dp.callback_query_handler(text='change', state=Dialog.style_photo)
async def change_photo(call: types.CallbackQuery):
    await call.message.answer('Пришли новое фото ***со стилем***.',
                              parse_mode='markdown')
    await call.answer()



