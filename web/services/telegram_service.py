import json

import aiohttp
import requests

from django.conf import settings


class TelegramService:
    def __init__(
            self,
            bot_token: str = settings.BOT_TOKEN,
            api_url: str = settings.TELEGRAM_API_URL
    ):
        self.__bot_token = bot_token
        self.api_url = api_url

    @property
    def __bot_api_url(self):
        return f'{self.api_url}/bot{self.__bot_token}'

    def send_message(
            self,
            chat_id: int,
            text: str,
            reply_markup: dict[str, list] | None = None,
            parse_mode: str = 'HTML',
    ):
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
        }

        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)

        response = requests.post(
            url=f'{self.__bot_api_url}/sendMessage',
            json=payload,
        )

        return response


class AsyncTelegramService:
    def __init__(
            self,
            bot_token: str = settings.BOT_TOKEN,
            api_url: str = settings.TELEGRAM_API_URL
    ):
        self.__bot_token = bot_token
        self.api_url = api_url
        self.__bot_api_url = f'{api_url}/bot{bot_token}'

    async def send_message(
            self,
            chat_id: int,
            text: str,
            reply_markup: dict[str, list] | None = None,
            parse_mode: str = 'HTML',
    ) -> int:
        url = f'{self.__bot_api_url}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
        }

        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                return response.status

    async def get_file_path_by_file_id(self, file_id: str):
        url = f'{self.__bot_api_url}/getFile'
        params = {"file_id": file_id}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:

                if response.status == 200:
                    file_path = (await response.json())['result']['file_path']
                    return file_path
                else:
                    raise Exception(f'Ошибка при получении file_path: {response.status}')

    async def save_file(self, file_id: str, save_path: str) -> int:
        file_path = await self.get_file_path_by_file_id(file_id)
        file_url = f'{self.api_url}/file/bot{self.__bot_token}/{file_path}'

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as file:
                        file.write(await response.read())
                else:
                    raise Exception(f"Ошибка при скачивании файла: {response.status}")

                return response.status


telegram_service = TelegramService()
async_telegram_service = AsyncTelegramService()
