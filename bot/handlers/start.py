import loguru
from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from yookassa import Payment as YooKassaPayment
from django.conf import settings

from bot.handlers.payment import successful_payment_handler
from bot.keyboards.inline import get_inline_keyboard
from web.apps.orders.models import Payment
from web.apps.telegram_users.models import TelegramUser

router = Router()


@router.message(CommandStart())
async def start_command_handler(
    message: types.Message,
    command: CommandObject,
):
    async def send_start_message():
        await message.answer(
            f'Привет, {message.from_user.first_name}.',
            reply_markup=get_inline_keyboard(
                buttons={
                    'Я заказчик': 'menu_user',
                    'Я таксист': 'menu_driver'
            }
        ))

    if not command.args or not command.args.startswith('payment_'):
        await send_start_message()
        return

    payment_id = int(command.args.split('_')[-1])
    payment: Payment = await Payment.objects.aget(
        id=payment_id
    )
    telegram_user: TelegramUser = await TelegramUser.objects.aget(telegram_id=message.from_user.id)

    if payment.telegram_user_id != telegram_user.id or payment.status == Payment.PAID:
        await send_start_message()
        return

    yookassa_payment = YooKassaPayment.find_one(payment.yookassa_payment_id)

    if not yookassa_payment.paid:
        await message.answer('Оплата не выполнена')
        return

    payment.status = Payment.PAID
    telegram_user.points += int(yookassa_payment.metadata.get('points'))

    await payment.asave()
    await telegram_user.asave()

    await successful_payment_handler(message, payment, yookassa_payment)






    
    
    

    
    

