from datetime import date, datetime
from typing import Union

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from django.utils import timezone

from bot.handlers.taxi_driver import is_car_approved_handler
from bot.keyboards.inline import get_inline_keyboard
from bot.keyboards.reply import get_reply_calendar_keyboard
from bot.states.statistic import DateState
from bot.utils.bot import edit_text_or_answer
from bot.utils.pagination import Paginator, get_pagination_buttons
from bot.utils import texts
from bot.utils.texts import get_order_info_message
from web.apps.orders.models import Order
from web.apps.telegram_users.models import TaxiDriver, TelegramUser

router = Router()

@router.callback_query(F.data.startswith('statistic_'))
async def statistic_callback_handler(callback: types.CallbackQuery):
    if not await is_car_approved_handler(callback):
        return
    page_number = int(callback.data.split('_')[-1])
    per_page = 5

    current_year = timezone.now().year
    years = sorted(
        list(range(2025, current_year + 1)),
        reverse=True
    )
    paginator = Paginator(
        array=years,
        page_number=page_number,
        per_page=per_page
    )
    buttons = {
        str(year): f'year_statistic_{year}_{page_number}'
        for year in paginator.get_page()
    }
    sizes = (1,) * per_page
    pagination_buttons = get_pagination_buttons(
        paginator, prefix='statistic'
    )
    if len(pagination_buttons.items()) == 1:
        sizes += (1, 1)
    else:
        sizes += (2, 1)

    buttons.update(pagination_buttons)
    buttons['Назад 🔙'] = 'menu_driver'

    await callback.message.edit_text(
        'Выберите год',
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes,
        )
    )


@router.callback_query(F.data.startswith('year_statistic_'))
async def year_statistic_callback_handler(
        callback: types.CallbackQuery,
):
    year, previous_page_number = map(int, callback.data.split('_')[-2:])
    now = timezone.now()
    year_months_names = texts.months if year != now.year else texts.months[:now.month]

    buttons = {
        month_name: f'month_statistic_{month_index + 1}_{year}'
        for month_index, month_name in enumerate(year_months_names)
    }
    buttons['Назад 🔙'] = f'statistic_{year}_{previous_page_number}'

    sizes = (1,) * (len(buttons))

    await callback.message.edit_text(
        'Выберите месяц',
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes,
        )
    )


@router.callback_query(F.data.startswith('month_statistic_'))
async def month_statistic_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
):
    month, year = map(int, callback.data.split('_')[-2:])

    await state.update_data(year=year, month=month)
    await state.set_state(DateState.day)

    await callback.message.delete()
    await callback.message.answer(
        'Выберите дату',
        reply_markup=get_reply_calendar_keyboard(
            year=year,
            month=month,
        )
    )


@router.message(F.text, DateState.day)
async def day_statistic_handler(
        message: types.Message,
        state: FSMContext,
):
    state_data = await state.get_data()
    year = state_data['year']
    month = state_data['month']

    try:
        day = int(message.text)
    except ValueError:
        await message.answer('Пожалуйста, выберите день из календаря.')
        return

    statistic_date = date(year=year, month=month, day=day)
    statistic_date_string = statistic_date.strftime("%d.%m.%Y")

    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=message.from_user.id,
    )
    orders = await Order.objects.afilter(
        driver_id=taxi_driver.id,
        created_at__date=statistic_date
    )
    if not orders:
        await message.answer(
            f'{statistic_date_string} нет заказов.'
        )
        return

    text = f'<b>Заказы на {statistic_date_string}</b>\n\n'

    total_profit = 0
    for order in orders[:10]:
        text += f'{get_order_info_message(order)}\n\n'
        total_profit += order.price

    buttons = {}
    if len(orders) > 10:
        buttons['Отправить всю статистику 📥'] = \
            f'send_statistic_{statistic_date_string}'
    else:
        text += f'Общая прибыль: <em><b>{int(total_profit)}</b> рублей</em>'


    buttons['Назад 🔙'] = f'month_statistic_{month}_{year}'

    await message.answer(
        text=text,
        reply_markup=get_inline_keyboard(buttons=buttons)
    )


@router.callback_query(F.data.startswith('send_statistic_'))
async def send_statistic_handler(
        callback: types.CallbackQuery,
):
    statistic_date_string = callback.data.split('_')[-1]
    statistic_date = datetime.strptime(
        statistic_date_string, '%d.%m.%Y'
    ).date()

    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    orders = await Order.objects.afilter(
        driver_id=taxi_driver.id,
        created_at__date=statistic_date
    )
    if not orders:
        await callback.message.answer(
            f'{statistic_date_string} нет заказов.'
        )
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    text = ''
    total_profit = 0
    for order in orders:
        if len(text) > 3500:
            await callback.message.answer(text)
            text = ''

        text += f'{get_order_info_message(order)}\n\n'
        total_profit += order.price

    await callback.message.answer(text)
    await callback.message.answer(f'Общая прибыль: <em><b>{total_profit}</b> рублей</em>')


