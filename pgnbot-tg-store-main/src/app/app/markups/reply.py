from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton


def build_keyboard_row(buttons: list):
    return [KeyboardButton(text=text) for text in buttons]


def build_keyboard(rows):
    return [build_keyboard_row(row) for row in rows]


main_menu_buttons = [["📦 Товары", "🛒 Корзина", "🔎 Поиск"], ["👤 Профиль", "🚦 Правила", "🛟 Поддержка"]]
main_menu = ReplyKeyboardMarkup(keyboard=build_keyboard(main_menu_buttons), resize_keyboard=True)


admin_menu = ReplyKeyboardMarkup(keyboard=build_keyboard([
    *main_menu_buttons,
    ["📢 Рассылка", "➕ Добавить товар", '💬 Сообщение'],
    ["➕ Добавить инвентарь"]
]), resize_keyboard=True)
