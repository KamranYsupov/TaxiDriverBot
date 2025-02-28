from typing import Dict, Tuple

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


def get_inline_keyboard(*, buttons: Dict[str, str], sizes: Tuple = (1, 2)):
    keyboard = InlineKeyboardBuilder()

    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

inline_driver_keyboard = get_inline_keyboard(
    buttons={
        'Смена 🧭': 'is_active',
        'Авто 🚖': 'car',
        'Детское кресло 🪑' : 'child_chair',
        'Тариф 💵': 'driver_tariff',
        'Статистика 📊': 'statistic'
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
