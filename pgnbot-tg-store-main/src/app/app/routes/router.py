from aiogram import Router

from app.middlewares.User import UserMiddleware
from app.routes.endpoints import basic_commands, order_commands
from app.routes.endpoints.admin import products as admin_products, notify
router = Router()

router.message.middleware(UserMiddleware())
router.callback_query.middleware(UserMiddleware())

router.include_router(basic_commands.router)
router.include_router(order_commands.router)
router.include_router(admin_products.router)
router.include_router(notify.router)
