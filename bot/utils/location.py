from typing import Tuple, Optional

from aiogram import types

from web.services.api_2gis import api_2gis_service


async def get_message_address(
        message: types.Message,
        city: Optional[str] = None,
) -> Tuple[str, Tuple[int, int]] | None:

    if message.text and not message.location:
        address_input = f'{city}, {message.text}' if city else message.text
        address, cords = api_2gis_service.find_match_address(address_input)

    elif message.location:
        location = message.location

        cords = (location.latitude, location.longitude)
        address = api_2gis_service.get_address_by_cords(
            lat=cords[0],
            lon=cords[1]
        )
    else:
        return None

    return address, cords