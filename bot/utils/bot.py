from aiogram import types
from aiogram.exceptions import TelegramBadRequest


async def edit_text_or_answer(
    message: types.Message,
    **kwargs,
):
    try:
        await message.edit_text(**message_data)
    except TelegramBadRequest:
        await message.answer(**message_data)
    