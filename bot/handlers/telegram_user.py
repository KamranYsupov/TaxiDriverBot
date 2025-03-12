from typing import Optional

from aiogram import Router, types, F
from asgiref.sync import sync_to_async

from bot.keyboards.inline import (
    get_inline_keyboard,
    get_inline_review_driver_keyboard
)
from bot.utils.bot import edit_text_or_answer
from bot.utils.texts import get_order_info_message
from web.apps.orders.models import Order
from web.apps.telegram_users.models import (
    TelegramUser,
    TaxiDriver,
    Car,
    TariffDriverRequest
)

router = Router()


@router.callback_query(F.data == 'tariff')
async def tariff_callback_handler(callback: types.CallbackQuery):
    telegram_user: TelegramUser = await TelegramUser.objects.aget(
        telegram_id=callback.from_user.id,
    )
    buttons = {}
    sizes = (1, ) * (len(TelegramUser.TARIFF_CHOICES) + 1)

    for tariff in TaxiDriver.TARIFF_CHOICES:
        button_text = tariff[-1]
        if telegram_user.tariff == tariff[0]:
            button_text += ' ✅'

        buttons[button_text] = f'change_tariff_{tariff[0]}'

    buttons.update({'Назад 🔙': 'menu_user',})
    await callback.message.edit_text(
        'Выберите тариф.',
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes
        )
    )


@router.callback_query(F.data.startswith('change_tariff_'))
async def change_tariff_callback_handler(callback: types.CallbackQuery):
    tariff = callback.data.split('_')[-1]
    telegram_user: TelegramUser = await TelegramUser.objects.aget(
        telegram_id=callback.from_user.id,
    )
    telegram_user.tariff = tariff
    await telegram_user.asave()

    await tariff_callback_handler(callback)