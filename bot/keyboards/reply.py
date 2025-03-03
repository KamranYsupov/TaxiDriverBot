import calendar
from typing import Sequence
from datetime import datetime

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from django.utils import timezone


def get_reply_keyboard(
    buttons: Sequence[str],
    resize_keyboard: bool = True,
) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=button_text)] for button_text in buttons]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=resize_keyboard
    )
    
def get_reply_contact_keyboard(
    text: str = 'Отправить номер телефона 📲'
) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=text, request_contact=True)],
        [KeyboardButton(text='Отмена ❌')]
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_reply_location_keyboard(
        text: str = 'Отправить геолокацию 🏬'
) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=text, request_location=True)],
        [KeyboardButton(text='Отмена ❌')]
    ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_reply_calendar_keyboard(
        year: int = timezone.now().year,
        month: int = timezone.now().month,
):
    cal = calendar.Calendar()

    # Получаем дни месяца в виде списка кортежей (год, месяц, день, день недели)
    month_days = cal.itermonthdays4(year, month)

    # Создаем клавиатуру
    keyboard = []

    # Добавляем заголовок с названием месяца и годом
    month_name = datetime(year, month, 1).strftime('%B %Y')
    keyboard.append([KeyboardButton(text=f' {month_name} ')])

    # Добавляем заголовок с днями недели
    week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    keyboard.append([KeyboardButton(text=f' {day} ') for day in week_days])
    # Добавляем дни месяца
    row = []
    for day in month_days:
        if day[1] == month:  # Проверяем, что день принадлежит текущему месяцу
            row.append(KeyboardButton(text=str(day[2])))
        else:
            row.append(KeyboardButton(text=' '))  # Пустая кнопка для дней предыдущего/следующего месяца

        if len(row) == 7:  # Добавляем строку в клавиатуру и начинаем новую строку
            keyboard.append(row)
            row = []

    # Добавляем последнюю строку, если она не пуста
    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text='Отмена ❌')])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


reply_cancel_keyboard = get_reply_keyboard(buttons=('Отмена ❌',))
reply_keyboard_remove = ReplyKeyboardRemove()
reply_contact_keyboard = get_reply_contact_keyboard()
reply_location_keyboard = get_reply_location_keyboard()

    
