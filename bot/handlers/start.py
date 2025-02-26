import loguru
from aiogram import Router, types
from aiogram.filters import CommandStart, Command

from bot.keyboards.inline import get_inline_keyboard

router = Router()


@router.message(CommandStart())
async def start_command_handler(
    message: types.Message,
):
    message_text = f'Привет, {message.from_user.first_name}.'
    await message.answer(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons={
                'Я заказчик': 'menu_user',
                'Я таксист': 'menu_driver'
            }
        ))
    
    
    

    
    

