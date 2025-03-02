from aiogram import Router, F, types

from bot.keyboards.inline import get_inline_keyboard
from web.apps.telegram_users.models import TaxiDriver, TelegramUser

router = Router()

@router.callback_query(F.data.startswith('review_'))
async def review_callback_handler(callback: types.CallbackQuery):
    user_type, review_mark, user_id = callback.data.split('_')[1:]

    if user_type == 'driver':
        user_obj: TaxiDriver = await TaxiDriver.objects.aget(id=user_id)
    elif user_type == 'user':
        user_obj: TelegramUser = await TelegramUser.objects.aget(id=user_id)
    else:
        return

    user_obj.reviews.append(int(review_mark))

    await user_obj.asave()

    await callback.message.edit_text(
        'Спасибо за вашу оценку ⭐️',
        reply_markup=None
    )


