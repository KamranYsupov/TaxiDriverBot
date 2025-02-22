import loguru
from aiogram import Router, types
from aiogram.filters import CommandStart, Command

router = Router()


@router.message(CommandStart())
async def start_command_handler(
    message: types.Message,
):
    message_text = f'Привет, {message.from_user.first_name}.'
    await message.answer(message_text)
    
    
    

    
    

