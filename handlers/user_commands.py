from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.inline import get_main_menu_keyboard
from keyboards.reply import get_main_reply_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    text = "👋 Привет! Я бот для управления заказами. Выберите действие:"
    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = "👋 Вы в главном меню. Выберите действие:"
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "<b>📖 Инструкция по использованию бота:</b>\n\n"
        "• <b>📝 Создать заказ</b> - пошаговое создание нового заказа.\n"
        "• <b>📋 Просмотреть заказы</b> - отображение всех ваших заказов с возможностью их редактирования и удаления.\n"
        "• <b>⚙️ Управление платформами</b> - добавление и удаление платформ, которые можно будет выбирать при создании заказа.\n\n"
        "• <b>/cancel</b> или кнопка <b>Главное меню</b> - отмена текущего действия и возврат в главное меню."
    )
    await message.answer(text)


@router.message(Command("cancel"))
# ИСПРАВЛЕНО: Убран фильтр на текст "Отмена"
@router.message(F.text == "Главное меню")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Действие отменено. Вы возвращены в главное меню.",
        reply_markup=get_main_reply_keyboard()
    )
    await cmd_start(message, state)


@router.message(F.text == "Таблица")
async def table_test_message(message: Message):
    await message.answer("📊 Функция экспорта в таблицу находится в разработке.")