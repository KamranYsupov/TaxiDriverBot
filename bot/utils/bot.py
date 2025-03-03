from aiogram import types
from aiogram.exceptions import TelegramBadRequest


async def edit_text_or_answer(
    message: types.Message,
    **kwargs,
):
    try:
        await message.edit_text(**kwargs)
    except TelegramBadRequest:
        await message.answer(**kwargs)
    