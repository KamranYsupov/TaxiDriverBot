import os

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from django.core.files.images import ImageFile

from bot.keyboards.inline import get_inline_keyboard, inline_driver_keyboard
from bot.keyboards.reply import reply_contact_keyboard, reply_keyboard_remove, reply_cancel_keyboard
from bot.states.taxi_driver import TaxiDriverState
from bot.valiators.taxi_driver import TaxiDriverStateValidator

from web.apps.telegram_users.models import TelegramUser, TaxiDriver
from web.services.telegram_service import async_telegram_service

router = Router()

@router.message(
    StateFilter('*'),
    F.text.lower() == 'отмена ❌'
)
async def cancel_handler(
        message: types.Message,
        state: FSMContext,
):
    await message.answer(
        'Действие отменено',
        reply_markup=reply_keyboard_remove,
    )
    await state.clear()


@router.callback_query(F.data.startswith('menu_'))
async def menu_callback_query_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    user_type = callback.data.split('_')[-1]
    message_text = 'Выберите действие.'
    if user_type == 'user':
        await TelegramUser.objects.aget_or_create(
            telegram_id=callback.from_user.id,
            defaults={'username': callback.from_user.username}
        )

        await callback.message.edit_text(
            message_text,
            reply_markup=get_inline_keyboard(
                buttons={
                'Заказать': 'order',
                'Маркет': 'market',
                'Тариф': 'change_tariff',
            })
        )
        return

    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id
    )
    if not taxi_driver:
        await state.set_state(TaxiDriverState.full_name)
        await callback.message.edit_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=None
        )
        await callback.message.answer(
            'Отправьте ваше ФИО',
            reply_markup=reply_cancel_keyboard,
        )
        return

    await callback.message.edit_text(
        message_text,
        reply_markup=inline_driver_keyboard
    )
    return


@router.message(TaxiDriverState.full_name, F.text)
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text
    reply_markup = None

    if TaxiDriverStateValidator.validate_full_name(full_name):
        await state.update_data(full_name=message.text)
        await state.set_state(TaxiDriverState.phone_number)
        answer_text = (
            'Для регистрации нажмите на кнопу ' 
            '<b>"Отправить номер телефона 📲"</b>, чтобы его отправить'
        )
        reply_markup = reply_contact_keyboard
    else:
        answer_text = '❌ Пожалуйста, введите полное ФИО через пробелы'

    await message.answer(
        answer_text,
        reply_markup=reply_markup,
    )


@router.message(TaxiDriverState.phone_number, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone_number=message.contact.phone_number)
    await state.set_state(TaxiDriverState.passport_data)

    await message.answer(
        '📄 Введите серию и номер паспорта '
        'через пробел.\n\n'
        '<b>Пример: 4510 123456</b>',
        reply_markup=reply_cancel_keyboard,
    )


@router.message(TaxiDriverState.passport_data)
async def process_passport_data(message: types.Message, state: FSMContext):
    passport_data = message.text

    if TaxiDriverStateValidator.validate_passport_data(passport_data):
        await state.update_data(passport_data=passport_data)
        await state.set_state(TaxiDriverState.passport_photo)
        answer_text = '📸 Теперь отправьте фото главной страницы паспорта'
    else:
        answer_text = '❌ Неверный формат. Пример: 4510 123456'

    await message.answer(answer_text)


@router.message(TaxiDriverState.passport_photo, F.content_type == types.ContentType.PHOTO)
async def process_passport_photo(message: types.Message, state: FSMContext):
    passport_photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    save_path = 'some_photo.jpg'

    await async_telegram_service.save_file(
        file_id=passport_photo_file_id,
        save_path=save_path
    )

    taxi_driver_data = {
        'telegram_id': message.from_user.id,
        'username': message.from_user.username,
        'full_name': data['full_name'],
        'phone_number': data['phone_number'],
        'passport_data': data['passport_data'],
    }
    taxi_driver = TaxiDriver(**taxi_driver_data)

    with open(save_path, 'rb') as file:
        taxi_driver.passport_photo = ImageFile(file)
        await taxi_driver.asave()
        os.remove(file.name)

    await state.clear()

    await message.answer(
        '✅ Регистрация завершена!',
        reply_markup=inline_driver_keyboard
    )


@router.message(TaxiDriverState.passport_photo)
async def incorrect_passport_photo(message: types.Message):
    await message.answer('❌ Пожалуйста, отправьте фотографию паспорта в виде изображения')
