# order_processing.py

from math import ceil
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_add_order, orm_get_orders, orm_get_order, orm_update_order,
    orm_delete_order, orm_get_platforms, orm_count_orders
)
from fsm.states import AddOrder, EditOrder
from keyboards.inline import (
    get_platform_selection_keyboard, get_order_confirmation_keyboard,
    get_delete_confirmation_keyboard, get_field_to_edit_keyboard, OrderCallback, PlatformCallback,
    Paginator, get_skip_keyboard, get_edit_action_keyboard, get_orders_list_keyboard,
    OrderSelectionCallback, get_order_details_keyboard
)
from utils.formatters import format_order_for_display, format_order_data_for_review
from handlers.user_commands import cb_main_menu

router = Router()

ORDERS_PER_PAGE = 5

# --- Новая логика пагинации ---

async def build_orders_list(session: AsyncSession, page: int = 1):
    offset = (page - 1) * ORDERS_PER_PAGE
    orders = await orm_get_orders(session, limit=ORDERS_PER_PAGE, offset=offset)
    total_orders = await orm_count_orders(session)
    total_pages = ceil(total_orders / ORDERS_PER_PAGE) if total_orders > 0 else 1
    
    text = f"📋 <b>Список ваших заказов</b> (Страница {page}/{total_pages})"
    keyboard = get_orders_list_keyboard(orders=orders, page=page, total_pages=total_pages)
    
    return text, keyboard

@router.callback_query(F.data == "view_orders")
async def view_orders_list_start(callback: CallbackQuery, session: AsyncSession):
    text, keyboard = await build_orders_list(session, page=1)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(Paginator.filter())
async def paginate_orders_list(callback: CallbackQuery, callback_data: Paginator, session: AsyncSession):
    text, keyboard = await build_orders_list(session, page=callback_data.page)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
    
# --- Просмотр, редактирование и удаление конкретного заказа ---

@router.callback_query(OrderSelectionCallback.filter())
async def view_order_details(callback: CallbackQuery, callback_data: OrderSelectionCallback, session: AsyncSession, state: FSMContext):
    await state.clear()
    order = await orm_get_order(session, callback_data.order_id)
    if not order:
        await callback.answer("❌ Заказ не найден, возможно, он был удален.", show_alert=True)
        await callback.message.delete()
        return

    text = format_order_for_display(order)
    keyboard = get_order_details_keyboard(order_id=order.id)
    await callback.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await callback.answer()

async def show_confirmation_summary(message: Message, state: FSMContext, edit_mode=False):
    data = await state.get_data()
    text = format_order_data_for_review(data)
    await state.set_state(AddOrder.confirmation)
    if edit_mode:
        await message.edit_text(text, reply_markup=get_order_confirmation_keyboard())
    else:
        await message.answer(text, reply_markup=get_order_confirmation_keyboard())

# --- Логика создания заказа (FSM) ---

@router.callback_query(F.data == "create_order")
async def create_order_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    platforms = await orm_get_platforms(session)
    if not platforms:
        await callback.answer("⚠️ Сначала нужно добавить хотя бы одну платформу.", show_alert=True)
        return
    await state.set_state(AddOrder.name)
    await callback.message.edit_text("📝 Введите название заказа:")
    await callback.answer()
    
@router.callback_query(F.data == "cancel_creation")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb_main_menu(callback, state)

@router.message(AddOrder.name)
async def get_order_name(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(name=message.text)
    platforms = await orm_get_platforms(session)
    await state.set_state(AddOrder.platform)
    await message.answer("👍 Отлично! Теперь выберите платформу:", reply_markup=get_platform_selection_keyboard(platforms))

@router.callback_query(AddOrder.platform, PlatformCallback.filter(F.action == "select_for_order"))
async def get_order_platform(callback: CallbackQuery, callback_data: PlatformCallback, state: FSMContext, session: AsyncSession):
    platform_id = callback_data.platform_id
    platforms = await orm_get_platforms(session)
    platform_name = next((p.name for p in platforms if p.id == platform_id), "Неизвестно")
    await state.update_data(platform_id=platform_id, platform_name=platform_name)
    await state.set_state(AddOrder.link)
    await callback.message.edit_text("🔗 Теперь отправьте ссылку или пропустите.", reply_markup=get_skip_keyboard("skip_link"))

@router.message(AddOrder.link)
async def get_order_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    await state.set_state(AddOrder.payment_status)
    await message.answer("💳 Какой статус оплаты?")

@router.callback_query(AddOrder.link, F.data == "skip_link")
async def skip_order_link(callback: CallbackQuery, state: FSMContext):
    await state.update_data(link=None)
    await state.set_state(AddOrder.payment_status)
    await callback.message.edit_text("💳 Какой статус оплаты?")
    await callback.answer()

@router.message(AddOrder.payment_status)
async def get_payment_status(message: Message, state: FSMContext):
    await state.update_data(payment_status=message.text)
    await state.set_state(AddOrder.comment)
    await message.answer("💬 Добавьте комментарий или пропустите.", reply_markup=get_skip_keyboard("skip_comment"))

@router.callback_query(AddOrder.comment, F.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await show_confirmation_summary(callback.message, state, edit_mode=True)
    await callback.answer()

@router.message(AddOrder.comment)
async def get_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_confirmation_summary(message, state, edit_mode=False)

@router.callback_query(AddOrder.confirmation, F.data == "confirm_save_order")
async def save_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await orm_add_order(session, data)
    await state.clear()
    await callback.answer("✅ Заказ успешно создан!", show_alert=True)
    await cb_main_menu(callback, state)

@router.callback_query(AddOrder.confirmation, F.data == "edit_before_save")
async def edit_order_before_save(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Какое поле вы хотите изменить?", reply_markup=get_field_to_edit_keyboard(order_id=0, for_creation=True))

@router.callback_query(F.data == "back_to_confirmation")
async def back_to_confirmation(callback: CallbackQuery, state: FSMContext):
    await show_confirmation_summary(callback.message, state, edit_mode=True)

@router.callback_query(F.data.startswith("edit_creation:"))
async def edit_creation_field_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    field = callback.data.split(":")[1]
    await state.update_data(editing_field=field)
    await state.set_state(AddOrder.editing_field)
    prompts = {"name": "Введите новое название:", "platform": "Выберите новую платформу:", "link": "Отправьте новую ссылку:", "payment_status": "Введите новый статус оплаты:", "comment": "Введите новый комментарий:"}
    markup = None
    if field == "platform":
        platforms = await orm_get_platforms(session)
        markup = get_platform_selection_keyboard(platforms)
    elif field in ["link", "comment"]:
        markup = get_edit_action_keyboard(back_callback="back_to_confirmation")
    await callback.message.edit_text(prompts[field], reply_markup=markup)

@router.callback_query(AddOrder.editing_field, F.data == "leave_empty")
async def leave_field_empty_creation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    field_to_edit = data.get("editing_field")
    await state.update_data({field_to_edit: None, "editing_field": None})
    await show_confirmation_summary(callback.message, state, edit_mode=True)

@router.message(AddOrder.editing_field)
async def get_new_field_value_creation(message: Message, state: FSMContext):
    data = await state.get_data()
    field_to_edit = data.get("editing_field")
    if not field_to_edit or field_to_edit == 'platform': return
    await state.update_data({field_to_edit: message.text, "editing_field": None})
    await show_confirmation_summary(message, state, edit_mode=False)

@router.callback_query(AddOrder.editing_field, PlatformCallback.filter(F.action == "select_for_order"))
async def get_new_platform_value_creation(callback: CallbackQuery, callback_data: PlatformCallback, state: FSMContext, session: AsyncSession):
    platform_id = callback_data.platform_id
    platforms = await orm_get_platforms(session)
    platform_name = next((p.name for p in platforms if p.id == platform_id), "Неизвестно")
    await state.update_data(platform_id=platform_id, platform_name=platform_name, editing_field=None)
    await show_confirmation_summary(callback.message, state, edit_mode=True)

@router.callback_query(OrderCallback.filter(F.action == "edit"))
async def edit_existing_order_start(callback: CallbackQuery, callback_data: OrderCallback, state: FSMContext):
    await state.set_state(EditOrder.select_field)
    await state.update_data(order_id=callback_data.order_id)
    await callback.message.edit_text("✏️ Какое поле вы хотите изменить?", reply_markup=get_field_to_edit_keyboard(order_id=callback_data.order_id, for_creation=False))

@router.callback_query(EditOrder.select_field, F.data.startswith("edit_existing:"))
async def edit_existing_field_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    field, order_id = parts[1], int(parts[2])
    await state.update_data(editing_field=field, order_id=order_id)
    await state.set_state(EditOrder.get_new_value)
    prompts = { "name": "Введите новое название:", "platform": "Выберите новую платформу:", "link": "Отправьте новую ссылку:", "payment_status": "Введите новый статус оплаты:", "comment": "Введите новый комментарий:" }
    markup = None
    if field == "platform":
        platforms = await orm_get_platforms(session)
        markup = get_platform_selection_keyboard(platforms)
    elif field in ["link", "comment"]:
        markup = get_edit_action_keyboard(back_callback=OrderSelectionCallback(order_id=order_id).pack())
    await callback.message.edit_text(prompts[field], reply_markup=markup)

# --- КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ ---

# ИЗМЕНЕНО: Хендлер для кнопки "Оставить пустым"
@router.callback_query(EditOrder.get_new_value, F.data == "leave_empty")
async def leave_field_empty_existing(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    field, order_id = data.get("editing_field"), data.get("order_id")
    
    # 1. Обновляем поле в БД, устанавливая его в None
    await orm_update_order(session, order_id, {field: None})
    
    # 2. Очищаем состояние FSM
    await state.clear()
    
    # 3. Получаем обновленный заказ из БД
    order = await orm_get_order(session, order_id)
    
    # 4. Редактируем сообщение с запросом, превращая его в обновленную карточку заказа
    text = format_order_for_display(order)
    keyboard = get_order_details_keyboard(order_id=order.id)
    await callback.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    
    # 5. Отправляем пользователю всплывающее уведомление
    await callback.answer("✅ Поле очищено!", show_alert=False)


# ИЗМЕНЕНО: Хендлер для получения нового текстового значения
@router.message(EditOrder.get_new_value)
async def get_new_value_for_existing_order(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    field, order_id = data.get("editing_field"), data.get("order_id")

    # 1. Обновляем поле в БД, устанавливая новое значение
    await orm_update_order(session, order_id, {field: message.text})
    
    # 2. Очищаем состояние FSM
    await state.clear()

    # 3. Получаем обновленный заказ из БД
    order = await orm_get_order(session, order_id)
    
    # 4. Отправляем НОВОЕ сообщение с обновленной карточкой заказа
    # (мы не можем редактировать сообщение пользователя, поэтому отправляем новое)
    text = format_order_for_display(order)
    keyboard = get_order_details_keyboard(order_id=order.id)
    await message.answer("✅ Поле обновлено!")
    await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)


@router.callback_query(EditOrder.get_new_value, PlatformCallback.filter(F.action == "select_for_order"))
async def get_new_platform_for_existing_order(callback: CallbackQuery, callback_data: PlatformCallback, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    order_id = data.get("order_id")
    await orm_update_order(session, order_id, {"platform_id": callback_data.platform_id})
    await state.clear()
    await callback.answer("✅ Платформа обновлена!", show_alert=True)
    await view_order_details(callback, OrderSelectionCallback(order_id=order_id), session, state)

@router.callback_query(OrderCallback.filter(F.action == "delete_prompt"))
async def delete_order_prompt(callback: CallbackQuery, callback_data: OrderCallback, session: AsyncSession):
    order = await orm_get_order(session, callback_data.order_id)
    if not order: return
    text = f"Вы уверены, что хотите удалить заказ '<b>{order.name}</b>'?"
    await callback.message.edit_text(text, reply_markup=get_delete_confirmation_keyboard(order.id))
    await callback.answer()
    
@router.callback_query(OrderCallback.filter(F.action == "delete_confirm"))
async def delete_order_confirm(callback: CallbackQuery, callback_data: OrderCallback, session: AsyncSession):
    await orm_delete_order(session, callback_data.order_id)
    await callback.answer("🗑️ Заказ удален.", show_alert=True)
    text, keyboard = await build_orders_list(session)
    await callback.message.edit_text(text, reply_markup=keyboard)