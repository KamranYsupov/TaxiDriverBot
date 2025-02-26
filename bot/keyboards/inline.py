from typing import Dict, Tuple

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


def get_inline_keyboard(*, buttons: Dict[str, str], sizes: Tuple = (1, 2)):
    keyboard = InlineKeyboardBuilder()

    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

inline_driver_keyboard = get_inline_keyboard(
    buttons={
        'Смена 🧭': 'in_work',
        'Авто 🚖': 'car',
        'Детское кресло 🪑' : 'child_chair',
        'Тариф 💵': 'tariff',
        'Статистика 📊': 'statistic'
    },
    sizes=(1, 1, 1, 1, 1)
)

inline_cancel_keyboard = get_inline_keyboard(
    buttons={'Отмена ❌': 'cancel'}
)
