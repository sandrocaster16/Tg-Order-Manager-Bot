from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline import get_platform_management_keyboard, get_delete_platform_keyboard, PlatformCallback
from database.orm_query import orm_add_platform, orm_get_platforms, orm_delete_platform
from fsm.states import AddPlatform, DeletePlatform
from handlers.user_commands import cmd_start # Используем для возврата в меню

router = Router()

@router.callback_query(F.data == "manage_platforms")
async def manage_platforms(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    
    # ИЗМЕНЕНО: Выводим список платформ перед меню
    platforms = await orm_get_platforms(session)
    if platforms:
        platform_list = "\n".join([f"{i+1}) {p.name}" for i, p in enumerate(platforms)])
        text = f"<b>⚙️ Ваши платформы:</b>\n{platform_list}\n\nВыберите действие:"
    else:
        text = "😕 У вас пока нет ни одной платформы.\n\nВыберите действие:"
        
    await callback.message.edit_text(
        text,
        reply_markup=get_platform_management_keyboard()
    )
    await callback.answer()

# --- Добавление платформы ---
@router.callback_query(F.data == "add_platform")
async def add_platform_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddPlatform.name)
    await callback.message.edit_text("Введите название новой платформы. Для отмены введите /cancel")
    await callback.answer()

@router.message(AddPlatform.name)
async def add_platform_name(message: Message, state: FSMContext, session: AsyncSession):
    platform_name = message.text.strip()
    try:
        await orm_add_platform(session, platform_name)
        await message.answer(f"✅ Платформа '<b>{platform_name}</b>' успешно добавлена.")
    except IntegrityError:
        await message.answer(f"⚠️ Платформа с названием '<b>{platform_name}</b>' уже существует.")
    
    # Возвращаемся в главное меню, чтобы показать обновленный список
    await cmd_start(message, state)

# --- Удаление платформы ---
@router.callback_query(F.data == "delete_platform_select")
async def delete_platform_select(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    platforms = await orm_get_platforms(session)
    if not platforms:
        await callback.answer("😕 Нет платформ для удаления.", show_alert=True)
        return
    
    await state.set_state(DeletePlatform.select)
    await callback.message.edit_text(
        "👇 Нажмите на платформу, чтобы удалить её:",
        reply_markup=get_delete_platform_keyboard(platforms)
    )
    await callback.answer()

@router.callback_query(DeletePlatform.select, PlatformCallback.filter(F.action == "delete"))
async def delete_platform_confirm(callback: CallbackQuery, callback_data: PlatformCallback, state: FSMContext, session: AsyncSession):
    try:
        await orm_delete_platform(session, callback_data.platform_id)
        await callback.answer("🗑️ Платформа удалена!", show_alert=True)
        
        platforms = await orm_get_platforms(session)
        if not platforms:
            await callback.message.edit_text("✅ Все платформы удалены.", reply_markup=get_platform_management_keyboard())
        else:
            await callback.message.edit_text(
                "👇 Нажмите на платформу, чтобы удалить её:",
                reply_markup=get_delete_platform_keyboard(platforms)
            )
    except IntegrityError:
        await callback.answer(
            "❌ Ошибка: Нельзя удалить платформу, так как она используется в заказах.", show_alert=True
        )
    except Exception as e:
        await callback.answer(f"Произошла неизвестная ошибка: {e}", show_alert=True)