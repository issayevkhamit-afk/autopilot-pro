from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


CANCEL_TEXT = {"ru": "❌ Отмена", "kz": "❌ Болдырмау", "uz": "❌ Bekor qilish", "kg": "❌ Жокко чыгаруу"}

# country → (currency, [(button_text, lang_code), ...])
COUNTRY_CONFIG = {
    "kz": ("KZT", [("🇷🇺 Русский", "ru"), ("🇰🇿 Қазақша", "kz")]),
    "uz": ("UZS", [("🇷🇺 Русский", "ru"), ("🇺🇿 O'zbekcha", "uz")]),
    "kg": ("KGS", [("🇷🇺 Русский", "ru"), ("🇰🇬 Кыргызча", "kg")]),
}


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Цены на работы", callback_data="admin:labor")],
        [InlineKeyboardButton(text="🖼 Загрузить логотип", callback_data="admin:logo")],
        [InlineKeyboardButton(text="⚙️ Настройки сервиса", callback_data="admin:settings")],
        [InlineKeyboardButton(text="📋 История смет", callback_data="admin:estimates")],
        [InlineKeyboardButton(text="👥 Сотрудники", callback_data="admin:workers")],
        [InlineKeyboardButton(text="🌍 Страна и язык", callback_data="admin:country")],
    ])


def country_picker_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇰🇿 Казахстан (KZT ₸)", callback_data="setcountry:kz")],
        [InlineKeyboardButton(text="🇺🇿 Узбекистан (UZS сум)", callback_data="setcountry:uz")],
        [InlineKeyboardButton(text="🇰🇬 Кыргызстан (KGS сом)", callback_data="setcountry:kg")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
    ])


def lang_for_country_kb(country: str) -> InlineKeyboardMarkup:
    _, langs = COUNTRY_CONFIG.get(country, COUNTRY_CONFIG["kz"])
    buttons = [
        [InlineKeyboardButton(text=text, callback_data=f"setlang:{code}:{country}")]
        for text, code in langs
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:country")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def language_picker_kb() -> InlineKeyboardMarkup:
    """Legacy — kept for back-compat, not shown in menu."""
    return country_picker_kb()


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
