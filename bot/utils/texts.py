from web.apps.orders.models import Order

address_string = (
    'улица Ленина 12 к3\n'
    'проспект Мира 10\n'
    'Невский проспект, 12\n'
    'улица Малышева, 20\n'
    'улица Баумана 12\n'
    'улица Дубровинского, 13\n'
)

months = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
]

def get_order_info_message(order: Order) -> str:
    order_info_message = (
        '<b>Тип: '
        f'<em>{"Такси 🚕" if order.type == Order.TAXI else "Доставка 📦"}</em></b>\n'
        f'<b>Адрес 1:</b> <em>{order.from_address}</em>\n'
        f'<b>Адрес 2:</b> <em>{order.to_address}</em>\n'
        f'<b>Cтоимость:</b> <em>{int(order.price)} руб.</em>\n'
    )

    return order_info_message