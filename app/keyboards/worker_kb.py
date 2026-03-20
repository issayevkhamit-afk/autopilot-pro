from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def estimate_confirm_kb(estimate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить и PDF", callback_data=f"estimate:confirm:{estimate_id}"),
            InlineKeyboardButton(text="🗑 Отмена", callback_data=f"estimate:cancel:{estimate_id}"),
        ],
    ])


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text="🔧 Новая смета")]]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Админ панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
