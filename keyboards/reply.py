from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_reply_keyboard():
    """Создает основную клавиатуру с кнопками внизу экрана."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Главное меню"),
                KeyboardButton(text="Таблица"),
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Используйте команды или меню..."
    )