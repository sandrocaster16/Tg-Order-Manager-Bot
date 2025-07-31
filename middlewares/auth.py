from typing import Callable, Dict, Any, Awaitable, Set
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.dispatcher.flags import get_flag
from aiogram.utils.chat_action import ChatActionSender

class AdminAuthMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: Set[int]):
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")

        if not user or user.id not in self.admin_ids:
            if isinstance(event, (Message, CallbackQuery)):
                 await event.answer("❌ У вас нет доступа к этому боту.", show_alert=isinstance(event, CallbackQuery))
            return

        return await handler(event, data)