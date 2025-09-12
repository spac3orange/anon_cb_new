from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.core import config_aiogram


def choose_sex():
    kb_builder = InlineKeyboardBuilder()
    kb_builder.button(text='Девушка', callback_data='sex_female')
    kb_builder.button(text='Парень', callback_data='sex_male')
    kb_builder.adjust(2)
    return kb_builder.as_markup(resize_keyboard=True)