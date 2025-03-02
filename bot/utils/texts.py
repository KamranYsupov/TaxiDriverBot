from web.apps.orders.models import Order, OrderType

address_string = (
    'Новосибирск, улица Ленина, 12\n'
    'Москва, проспект Мира, 12а\n'
    'Санкт-Петербург, Невский проспект, 12/3\n'
    'Екатеринбург, улица Малышева, 12-А\n'
    'Казань, улица Баумана, 12 корпус 3\n'
    'Красноярск, улица Дубровинского, 12 строение 5\n'
    'Новосибирск, улица Ленина, 12/3 корпус 2\n'
)


def get_order_info_message(order: Order) -> str:
    order_info_message = (
        '<b>Тип:</b> '
        f'<em>{"Такси 🚕" if order.type == OrderType.TAXI else "Доставка 📦"}</em>\n'
        f'<b>Адрес 1:</b> <em>{order.from_address}</em>\n'
        f'<b>Адрес 2:</b> <em>{order.to_address}</em>\n\n'
        f'<b>Cтоимость:</b> <em>{order.price} руб.</em>\n'
    )

    return order_info_message