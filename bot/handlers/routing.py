from aiogram import Router

from .start import router as start_router
from .register import router as register_router
from .car import router as car_router
from .taxi_driver import router as taxi_driver_router

def get_main_router():
    main_router = Router()

    main_router.include_router(start_router)
    main_router.include_router(register_router)
    main_router.include_router(car_router)
    main_router.include_router(taxi_driver_router)

    return main_router