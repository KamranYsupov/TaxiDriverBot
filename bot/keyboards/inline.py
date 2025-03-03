from typing import Dict, Tuple, Union

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from web.apps.telegram_users.models import TaxiDriver, TelegramUser


def get_inline_keyboard(
        *,
        buttons: Dict[str, str],
        sizes: Tuple = (1, 2)
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


def get_inline_review_keyboard(
        prefix: str,
        user_id: Union[TaxiDriver.id, TelegramUser.id]
) -> InlineKeyboardMarkup:

    inline_keyboard = get_inline_keyboard(
        buttons={f'{i} ⭐️': f'review_{prefix}_{i}_{user_id}' for i in range(1, 6)},
        sizes=(1,)
    )

    return inline_keyboard


def get_inline_review_driver_keyboard(
        driver_id: TaxiDriver.id
) -> InlineKeyboardMarkup:
    return get_inline_review_keyboard(
        prefix='driver',
        user_id=driver_id
    )


def get_inline_review_telegram_user_keyboard(
        telegram_user_id: TelegramUser.id
) -> InlineKeyboardMarkup:
    return get_inline_review_keyboard(
        prefix='user',
        user_id=telegram_user_id
    )


inline_driver_keyboard = get_inline_keyboard(
    buttons={
        'Смена 🧭': 'is_active',
        'Авто 🚖': 'car',
        'Детское кресло 🪑' : 'child_chair',
        'Тариф 💵': 'driver_tariff',
        'Статистика 📊': 'statistic_1'
    },
    sizes=(1, 1, 1, 1, 1)
)

inline_user_keyboard = get_inline_keyboard(
    buttons={
        'Заказать 🚖': 'order',
        'Маркет 📦': 'market',
        'Тариф 💵': 'change_tariff',
    }
)

inline_cancel_keyboard = get_inline_keyboard(
    buttons={'Отмена ❌': 'cancel'}
)
