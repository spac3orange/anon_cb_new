from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu() -> ReplyKeyboardMarkup:
    """
    Создает Reply-клавиатуру с кнопкой '🔍 Поиск собеседника'
    """
    keyboard = [
        [KeyboardButton(text="🔍 Поиск собеседника")],
        # Можно добавить другие кнопки, например:
        # [KeyboardButton(text="📊 Статистика")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,  # Клавиатура подстраивается под размер экрана
        one_time_keyboard=True,  # Не скрывать после нажатия
        input_field_placeholder="Выберите действие..."  # Подсказка в поле ввода
    )