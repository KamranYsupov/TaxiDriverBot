from enum import Enum
from typing import Tuple, Union, Dict

import requests

from django.conf import settings


class TransportEnum(Enum):
    TAXI = 'taxi'
    DRIVING = 'driving'
    WALKING = 'walking'
    BYCYCLE = 'bicycle'
    SCOOTER = 'scooter'
    EMERGENCY = 'emergency'
    TRUCK = 'truck'


class TrafficModeEnum(Enum):
    JAM = 'jam'
    STATISTICS = 'statistics'


class RouteModeEnum(Enum):
    FASTEST = 'fastest'
    SHORTEST = 'shortest'


class API2GisError(ValueError):
    pass


class API2GisService:
    """2GIS API Servie"""
    def __init__(self, api_key: str = settings.API_2GIS_KEY):
        self.__api_key = api_key

    def get_cords(
            self,
            address: str,
        return_data: bool = False,
    ) -> Tuple[float, float]:
        """Преобразует адрес в координаты (широта, долгота)."""

        url = 'https://catalog.api.2gis.com/3.0/items/geocode'
        params = {
            'q': address,
            'fields': 'items.point',
            'key': self.__api_key
        }
        response = requests.get(url, params=params)
        response_data = response.json()

        if 'result' not in response_data or not response_data['result']['items']:
            raise API2GisError(f'Адрес не найден: {address}')

        if return_data:
            return response_data

        lat = response_data['result']['items'][0]['point']['lat']
        lon = response_data['result']['items'][0]['point']['lon']

        return lat, lon

    def get_route_distance_and_duration(
            self,
            from_lat: float,
            from_lon: float,
            to_lat: float,
            to_lon: float,
            route_mode: RouteModeEnum = RouteModeEnum.FASTEST,
            traffic_mode: TrafficModeEnum = TrafficModeEnum.JAM,
            transport: TransportEnum = TransportEnum.TAXI,
            return_data: bool = False,
    ) -> Union[Tuple[float, float], Dict]:
        """Рассчитывает расстояние и продолжительность пути по дорогам между двумя точками."""

        url = 'http://routing.api.2gis.com/routing/7.0.0/global'
        params = {
            'key': self.__api_key
        }
        payload = {
            'points': [
                {
                    'lat': from_lat,
                    'lon': from_lon,
                    'type': 'stop',
                },
                {
                    'lat': to_lat,
                    'lon': to_lon,
                    'type': 'stop',
                }
            ],
            'route_mode': route_mode.value,
            'traffic_mode': traffic_mode.value,
            'transport': transport.value,
            'output': 'summary'
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, params=params, json=payload, headers=headers)
        response_data = response.json()

        if 'result' not in response_data:
            raise API2GisError('Ошибка при расчете маршрута')

        if return_data:
            return response_data

        length = response_data['result'][0]['length'] # Дистанция в метрах
        duration = response_data['result'][0]['duration'] # Время поездки в секундах

        return length, duration


    def get_address(
            self,
            lat: float,
            lon: float,
            return_data: bool = False
    ) -> Union[str, Dict]:
        """Получает адрес по координатам через 2GIS API."""

        url = 'https://catalog.api.2gis.com/3.0/items/geocode'
        params = {
            'lat': lat,  # Широта
            'lon': lon,  # Долгота
            'fields': 'items.address',
            'key': self.__api_key
        }

        response = requests.get(url, params=params)
        response_data = response.json()

        not_found_exc = API2GisError('Адрес не найден')

        if 'result' not in response_data or not response_data['result']['items']:
            raise not_found_exc

        if return_data:
            return response_data

        try:
            address_data = response_data['result']['items'][0]
            city: str = address_data['full_name'].split(',')[0]
            street_and_house = address_data['address_name']
        except KeyError:
            raise not_found_exc

        address_string = f'{city}, {street_and_house}'  # Город, Улица, Дом
        return address_string


api_2gis_service = API2GisService()