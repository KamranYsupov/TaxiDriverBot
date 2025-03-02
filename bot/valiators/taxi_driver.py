import re


class TaxiDriverStateValidator:
    """Класс валидатор для TaxiDriverState"""
    @staticmethod
    def validate_full_name(value: str) -> bool:
        if len(value.split()) < 2:
            return False

        return True

    @staticmethod
    def validate_passport_data(value: str) -> bool:
        series, number = value.split()
        if len(series) != 4 or len(number) != 6 or not series.isdigit() or not number.isdigit():
            return False

        return True


class CarStateValidator:
    """Класс валидатор для CarState"""
    @staticmethod
    def validate_name(value: str) -> bool:
        if len(value.strip()) < 2:
            return False

        return True

    @staticmethod
    def validate_gos_number(value: str) -> bool:
        if len(value) > 20:
            return False

        return True

    @staticmethod
    def validate_vin(value: str) -> bool:
        if len(value) != 17 or not value.isalnum():
            return False

        return True


class OrderStateValidator:
    """Класс валидатор для OrderState"""

    @staticmethod
    def validate_to_address(value: str):
        pattern = r'^[А-Яа-яёЁ\s-]+, [А-Яа-яёЁ\s-]+, \d+[А-Яа-яёЁ\/\-]*(?: корпус \d+)?(?: строение \d+)?$'

        if re.match(pattern, value):
            return True

        return False

