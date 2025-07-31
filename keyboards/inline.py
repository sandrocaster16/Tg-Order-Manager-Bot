from math import ceil
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class OrderCallback(CallbackData, prefix="order"):
    action: str
    order_id: int

class PlatformCallback(CallbackData, prefix="platform"):
    action: str
    platform_id: int
    
class Paginator(CallbackData, prefix="pag"):
    action: str
    page: int
    
class OrderSelectionCallback(CallbackData, prefix="sel_ord"):
    order_id: int

def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать заказ", callback_data="create_order")
    builder.button(text="📋 Просмотреть заказы", callback_data="view_orders")
    builder.button(text="⚙️ Управление платформами", callback_data="manage_platforms")
    builder.adjust(1)
    return builder.as_markup()

def get_orders_list_keyboard(orders: list, page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    
    for order in orders:
        builder.button(
            text=f"🏷️ {order.name}",
            callback_data=OrderSelectionCallback(order_id=order.id).pack()
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=Paginator(action="prev", page=page-1).pack()))
    
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=Paginator(action="next", page=page+1).pack()))
        
    builder.adjust(1)
    builder.row(*nav_buttons, width=3)
    builder.row(InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu"))
    
    return builder.as_markup()


def get_order_details_keyboard(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=OrderCallback(action="edit", order_id=order_id).pack())
    builder.button(text="🗑️ Удалить", callback_data=OrderCallback(action="delete_prompt", order_id=order_id).pack())
    builder.button(text="⬅️ К списку заказов", callback_data="view_orders")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_delete_confirmation_keyboard(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=OrderCallback(action="delete_confirm", order_id=order_id).pack())
    builder.button(text="⬅️ Нет, назад", callback_data=OrderSelectionCallback(order_id=order_id).pack()) # Возврат к деталям
    return builder.as_markup()

def get_platform_management_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить платформу", callback_data="add_platform")
    builder.button(text="➖ Удалить платформу", callback_data="delete_platform_select")
    builder.button(text="⬅️ Назад в меню", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()

def get_platform_selection_keyboard(platforms):
    builder = InlineKeyboardBuilder()
    for platform in platforms:
        builder.button(
            text=platform.name,
            callback_data=PlatformCallback(action="select_for_order", platform_id=platform.id).pack()
        )
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    builder.adjust(2)
    return builder.as_markup()

def get_skip_keyboard(skip_callback_data: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Пропустить", callback_data=skip_callback_data)
    return builder.as_markup()

def get_edit_action_keyboard(back_callback: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑️ Оставить пустым", callback_data="leave_empty")
    builder.button(text="⬅️ Назад", callback_data=back_callback)
    builder.adjust(1)
    return builder.as_markup()

def get_delete_platform_keyboard(platforms):
    builder = InlineKeyboardBuilder()
    for platform in platforms:
        builder.button(
            text=f"❌ {platform.name}",
            callback_data=PlatformCallback(action="delete", platform_id=platform.id).pack()
        )
    builder.button(text="⬅️ Назад", callback_data="manage_platforms")
    builder.adjust(1)
    return builder.as_markup()

def get_order_confirmation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Сохранить", callback_data="confirm_save_order")
    builder.button(text="✏️ Изменить поле", callback_data="edit_before_save")
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    builder.adjust(1)
    return builder.as_markup()
    
def get_field_to_edit_keyboard(order_id: int, for_creation=False):
    builder = InlineKeyboardBuilder()
    prefix = "edit_creation" if for_creation else "edit_existing"
    fields = { "name": "Название", "platform": "Платформу", "link": "Ссылку", "payment_status": "Статус оплаты", "comment": "Комментарий"}
    for field, text in fields.items():
        cb_data = f"{prefix}:{field}"
        if not for_creation: cb_data += f":{order_id}"
        builder.button(text=text, callback_data=cb_data)
    back_cb = "back_to_confirmation" if for_creation else OrderSelectionCallback(order_id=order_id).pack()
    builder.button(text="⬅️ Назад", callback_data=back_cb)
    builder.adjust(2)
    return builder.as_markup()