import time
from typing import Dict, Coroutine

from loguru import logger
from aiogram.types import Message
from django.conf import settings


async def rate_limit_middleware(
    handler: Coroutine,
    event: Message,
    data: Dict
):
    """Middleware для ограничения отправки сообщений пользователем боту."""

    user_id = event.from_user.id
    current_time = time.time()

    if not hasattr(rate_limit_middleware, 'users'):
        rate_limit_middleware.users = {}

    if user_id not in rate_limit_middleware.users:
        rate_limit_middleware.users[user_id] = {
            'last_message_time': current_time,
            'warning_sent': False
        }
        return await handler(event, data)

    user_data = rate_limit_middleware.users[user_id]
    last_message_time = user_data['last_message_time']

    if current_time - last_message_time < settings.MAX_MESSAGE_PER_SECOND:
        if not user_data['warning_sent']:
            await event.answer('Слишком много сообщений! Попробуйте позже.')
            user_data['warning_sent'] = True 
        return  

    user_data['last_message_time'] = current_time
    user_data['warning_sent'] = False  
    return await handler(event, data)
