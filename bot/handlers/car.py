import os

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from django.core.files.images import ImageFile

from bot.keyboards.inline import get_inline_keyboard, inline_driver_keyboard
from bot.keyboards.reply import reply_keyboard_remove, reply_cancel_keyboard
from bot.states.taxi_driver import CarState
from bot.valiators.taxi_driver import CarStateValidator

from web.apps.telegram_users.models import TelegramUser, TaxiDriver, Car
from web.services.telegram import async_telegram_service

router = Router()

@router.callback_query(F.data == 'car')
async def car_callback_handler(callback: types.CallbackQuery):
    taxi_driver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    car = await Car.objects.aget(driver=taxi_driver)

    buttons = {}
    if not car or car.status == Car.DISAPPROVED:
        buttons['Регистрация авто'] = 'add_car'
        message_text = 'Выберите действие'

    elif car.status == Car.APPROVED:
        message_text = f'Текущее авто: <b>{car.name}</b>'
        buttons['Смена авто'] = 'add_car'
    else:
        message_text = 'Ожидайте. Авто на проверке.'


    buttons.update({'Назад 🔙': 'menu_driver'})

    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(buttons=buttons)
    )


@router.callback_query(F.data == 'add_car')
async def add_car_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
):
    await callback.message.edit_reply_markup(
        callback.inline_message_id,
        reply_markup=None
    )
    await callback.message.answer(
        'Отправьте название авто',
        reply_markup=reply_cancel_keyboard
    )
    await state.set_state(CarState.name)


@router.message(CarState.name, F.text)
async def process_name(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer(' Имя должно содержать минимум 2 символа')
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(CarState.gos_number)
    await message.answer('🚖 Теперь введите гос. номер авто в формате А123АА123')


@router.message(CarState.gos_number)
async def process_gos_number(message: types.Message, state: FSMContext):
    gos_number = message.text
    if await Car.objects.afilter(gos_number=gos_number, status=Car.APPROVED):
        await message.answer('❌ Авто с таким номером уже существует')
        return

    await state.update_data(gos_number=gos_number)
    await state.set_state(CarState.vin)
    await message.answer('🔢 Введите VIN-номер автомобиля (17 символов)')


@router.message(CarState.vin)
async def process_vin(message: types.Message, state: FSMContext):
    vin = message.text.upper().strip()
    if not CarStateValidator.validate_vin(vin):
        await message.answer('❌ VIN должен состоять из 17 букв и цифр')
        return

    if await Car.objects.afilter(vin=vin, status=Car.APPROVED):
        await message.answer('❌ Авто с таким VIN уже существует')
        return

    await state.update_data(vin=vin)
    await state.set_state(CarState.photo)
    await message.answer('📸 Отправьте фото автомобиля')


@router.message(CarState.photo, F.content_type == types.ContentType.PHOTO)
async def process_photo(message: types.Message, state: FSMContext):
    taxi_driver = await TaxiDriver.objects.aget(
        telegram_id=message.from_user.id
    )
    car_photo_id = message.photo[-1].file_id
    data = await state.get_data()

    car_data = {
        'name': data['name'],
        'gos_number': data['gos_number'],
        'vin': data['vin'],
    }
    car = Car(**car_data)

    save_path = f'{car.name}.jpg'

    await async_telegram_service.save_file(
        file_id=car_photo_id,
        save_path=save_path
    )

    with open(save_path, 'rb') as file:
        car.photo = ImageFile(file)
        await car.asave()
        os.remove(file.name)

    taxi_driver.car_id = car.id
    await taxi_driver.asave()
    await state.clear()
    await message.answer_photo(
        photo=car_photo_id,
        caption=f'Ожидайте. Авто на проверке.\n\n'
                f'<b>Название</b>: {car.name}\n'
                f'<b>Гос. номер</b>: {car.gos_number}\n'
                f'<b>VIN</b>: {car.vin}',
        reply_markup=reply_keyboard_remove
    )


@router.message(CarState.photo)
async def invalid_photo(message: types.Message):
    await message.answer('❌ Пожалуйста, отправьте фото автомобиля')






