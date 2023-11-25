from abc import ABC
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from app.db.mongodb import engine
from app.models import User


class AdminMiddleware(BaseMiddleware, ABC):
    def __init__(self) -> None:
        pass

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        if data.get('user') and data['user'].is_admin:
            return await handler(event, data)

        user_data = await engine['users'].find_one({'id': event.from_user.id})

        if user_data and user_data.get('is_admin'):
            user = User(**user_data)
            data['user'] = user
            return await handler(event, data)
        else:
            await event.answer('You are not admin')
