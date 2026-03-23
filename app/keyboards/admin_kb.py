from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


CANCEL_TEXT = {"ru": "❌ Отмена", "kz": "❌ Болдырмау"}


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Цены на работы", callback_data="admin:labor")],
        [InlineKeyboardButton(text="🖼 Загрузить логотип", callback_data="admin:logo")],
        [InlineKeyboardButton(text="⚙️ Настройки сервиса", callback_data="admin:settings")],
        [InlineKeyboardButton(text="📋 История смет", callback_data="admin:estimates")],
        [InlineKeyboardButton(text="👥 Сотрудники", callback_data="admin:workers")],
        [InlineKeyboardButton(text="🌐 Язык интерфейса", callback_data="admin:language")],
    ])


def language_picker_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru"),
            InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="setlang:kz"),
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang:uz"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
    ])


def admin_prices_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить работу", callback_data="labor:add")],
        [InlineKeyboardButton(text="📋 Список работ", callback_data="labor:list")],
        [InlineKeyboardButton(text="🗑 Удалить работу", callback_data="labor:delete")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
    ])


def admin_settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Название сервиса", callback_data="settings:name")],
        [InlineKeyboardButton(text="📍 Город", callback_data="settings:city")],
        [InlineKeyboardButton(text="📞 Телефон", callback_data="settings:phone")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
    ])


def cancel_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT.get(lang, "❌ Отмена"))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
