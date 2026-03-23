from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from app.i18n import t


def language_picker_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kz"),
    ]])


def main_menu_kb(is_admin: bool = False, lang: str = "ru") -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text=t("btn_new_estimate", lang))]]
    if is_admin:
        buttons.append([KeyboardButton(text=t("btn_admin_panel", lang))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def payment_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_pay", lang), callback_data="pay:start"),
    ]])


def paid_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("btn_paid", lang), callback_data="pay:confirm_user"),
    ]])


def estimate_confirm_kb(estimate_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("btn_confirm_pdf", lang),
            callback_data=f"estimate:confirm:{estimate_id}",
        ),
        InlineKeyboardButton(
            text=t("btn_cancel_estimate", lang),
            callback_data=f"estimate:cancel:{estimate_id}",
        ),
    ]])
