from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Цены на работы", callback_data="admin:labor")],
        [InlineKeyboardButton(text="🔩 Прайс запчастей", callback_data="admin:parts")],
        [InlineKeyboardButton(text="🖼 Загрузить логотип", callback_data="admin:logo")],
        [InlineKeyboardButton(text="⚙️ Настройки сервиса", callback_data="admin:settings")],
        [InlineKeyboardButton(text="📋 История смет", callback_data="admin:estimates")],
        [InlineKeyboardButton(text="👥 Сотрудники", callback_data="admin:workers")],
    ])


def admin_prices_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить работу", callback_data="labor:add")],
        [InlineKeyboardButton(text="📋 Список работ", callback_data="labor:list")],
        [InlineKeyboardButton(text="🗑 Удалить работу", callback_data="labor:delete")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
    ])


def admin_parts_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Загрузить CSV/Excel", callback_data="parts:upload")],
        [InlineKeyboardButton(text="➕ Добавить вручную", callback_data="parts:add")],
        [InlineKeyboardButton(text="📋 Список запчастей", callback_data="parts:list")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
    ])


def admin_settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Название сервиса", callback_data="settings:name")],
        [InlineKeyboardButton(text="📍 Город", callback_data="settings:city")],
        [InlineKeyboardButton(text="📞 Телефон", callback_data="settings:phone")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
    ])


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
