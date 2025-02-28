from typing import Optional

from aiogram import Router, types, F


from bot.keyboards.inline import get_inline_keyboard
from web.apps.telegram_users.models import TelegramUser, TaxiDriver, Car, TariffDriverRequest

router = Router()


async def is_car_approved_handler(
        callback: types.CallbackQuery,
        car: Optional[Car] = None
):
    if not car:
        taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
            telegram_id=callback.from_user.id,
        )
        car: Car = await Car.objects.aget(driver=taxi_driver)

    if not car or car.status == Car.DISAPPROVED:
        message_text = 'Сначала зарегестрируйте авто'
    elif car.status == Car.WAITING:
        message_text = 'Ожидайте. Авто на проверке.'
    else:
        return True

    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons={'Назад 🔙': 'menu_driver'}
        )
    )


async def is_tariff_request_approved_handler(
        callback: types.CallbackQuery,
        tariff_request: TariffDriverRequest
):
    if tariff_request.status == Car.APPROVED:
        return True

    if tariff_request.status == Car.WAITING:
        message_text = 'Ожидайте. Авто на проверке.'
    else:
        message_text = 'Сначала зарегестрируйте авто'

    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons={'Назад 🔙': 'menu_driver'}
        )
    )

@router.callback_query(F.data == 'child_chair')
async def child_chair_callback_handler(callback: types.CallbackQuery):
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    car: Car = await Car.objects.aget(driver=taxi_driver)

    if not await is_car_approved_handler(callback, car):
        return

    button_text = 'Включить ✅' if not taxi_driver.child_chair else 'Выключить ❌'
    message_text = (
        'Детское кресло: '
        f'<b>{"включено ✅" if taxi_driver.child_chair else "выключено ❌"}</b>'
    )
    buttons = {
        button_text: 'driver_change-child_chair',
        'Назад 🔙': 'menu_driver',
    }

    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=(1, 1, 1)
        ),
    )


@router.callback_query(F.data == 'is_active')
async def is_active_callback_handler(callback: types.CallbackQuery):
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    car: Car = await Car.objects.aget(driver=taxi_driver)

    if not await is_car_approved_handler(callback, car):
        return

    button_text = 'Включить ✅' if not taxi_driver.is_active else 'Выключить ❌'
    message_text = (
        'Смена: '
        f'<b>{"включена ✅" if taxi_driver.is_active else "выключена ❌"}</b>'
    )
    buttons = {
        button_text: 'driver_change-is_active',
        'Назад 🔙': 'menu_driver',
    }

    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=(1, 1, 1)
        ),
    )


@router.callback_query(F.data.startswith('driver_change-'))
async def driver_change_field_callback_handler(callback: types.CallbackQuery):
    change_field_name = callback.data.split('-')[-1]
    if change_field_name not in ('child_chair', 'is_active'):
        return

    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    change_field_value = getattr(taxi_driver, change_field_name)  # Достаём значение нужного поля
    setattr(taxi_driver, change_field_name, not change_field_value)  # Изменяем значение нужного поля

    await taxi_driver.asave()

    if change_field_name == 'child_chair':
        await child_chair_callback_handler(callback)
    elif change_field_name == 'is_active':
        await is_active_callback_handler(callback)


@router.callback_query(F.data == 'driver_tariff')
async def driver_tariff_callback_handler(callback: types.CallbackQuery):
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    if not await is_car_approved_handler(callback):
        return

    buttons = {}
    sizes = (1, ) * (len(TaxiDriver.TARIFF_CHOICES) + 1)

    for tariff in TaxiDriver.TARIFF_CHOICES:
        button_text = tariff[-1]
        if taxi_driver.tariff == tariff[0]:
            button_text += ' ✅'

        buttons[button_text] = f'request_tariff_{tariff[0]}'


    buttons.update({'Назад 🔙': 'menu_driver',})
    await callback.message.edit_text(
        'Выберите тариф.',
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes
        )
    )


@router.callback_query(F.data.startswith('request_tariff_'))
async def request_tariff_callback_handler(callback: types.CallbackQuery):
    tariff = callback.data.split('_')[-1]
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    if taxi_driver.tariff == tariff:
        return

    print(tariff)

    tariff_request_kwargs = dict(
        driver=taxi_driver,
        tariff=tariff,
        status=TariffDriverRequest.WAITING,
    )
    tariff_requests = await TariffDriverRequest.objects.afilter(**tariff_request_kwargs)

    if tariff_requests:
        message_text = 'Вы уже отправили запрос. Ожидайте ответа администрации.'
    else:
        await TariffDriverRequest.objects.acreate(**tariff_request_kwargs)
        message_text = '✅ Ваша заявка успешно отправлена! Ожидайте ответа администрации.'


    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(buttons={'Назад 🔙': 'menu_driver'})
    )










