from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from app.db.mongodb import engine
from app.models import User


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = await engine['users'].find_one({"id": event.from_user.id})

        if user and user.get('is_banned', False):
            print("This user is banned", event.from_user.model_dump())
            return
        if user:
            data['user'] = User(**user)
        await handler(event, data)
