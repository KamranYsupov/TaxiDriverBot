from aiogram import Router

from .start import router as start_router
from .register import router as register_router
from .car import router as car_router
from .taxi_driver import router as taxi_driver_router
from .order import router as order_router
from .payment import router as payment_router
from .reviews import router as reviews_router
from .statistic import router as statistic_router

def get_main_router():
    main_router = Router()

    main_router.include_router(start_router)
    main_router.include_router(register_router)
    main_router.include_router(car_router)
    main_router.include_router(taxi_driver_router)
    main_router.include_router(order_router)
    main_router.include_router(payment_router)
    main_router.include_router(reviews_router)
    main_router.include_router(statistic_router)

    return main_router