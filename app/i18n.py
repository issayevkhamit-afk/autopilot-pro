"""RU / KZ translations. Usage: t('key', lang='ru', name='X')"""

TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        # Language picker
        "choose_language": "🌐 Выберите язык интерфейса:",
        "btn_ru": "🇷🇺 Русский",
        "btn_kz": "🇰🇿 Қазақша",
        "btn_uz": "🇺🇿 O'zbekcha",
        "btn_kg": "🇰🇬 Кыргызча",
        "language_set_ru": "✅ Язык установлен: Русский",
        "language_set_kz": "✅ Язык установлен: Қазақша",
        "language_set_uz": "✅ Язык установлен: O'zbekcha",
        "language_set_kg": "✅ Язык установлен: Кыргызча",
        "country_set_kz": "🇰🇿 Страна: Казахстан | Валюта: KZT ₸\nВыберите язык:",
        "country_set_uz": "🇺🇿 Страна: Узбекистан | Валюта: UZS сум\nВыберите язык:",
        "country_set_kg": "🇰🇬 Страна: Кыргызстан | Валюта: KGS сом\nВыберите язык:",
        "choose_country": "🌍 Выберите страну и валюту:",
        # Start
        "welcome_no_shop": (
            "👋 Добро пожаловать в *AutoPilot Pro*!\n\n"
            "Для подключения к автосервису используйте пригласительную ссылку "
            "или создайте свой сервис командой /newshop"
        ),
        "greeting": "👋 Привет, *{name}*!\n\n🏪 Сервис: *{shop}*\n👤 Роль: _{role}_\n\n{tip}",
        "role_admin": "Администратор",
        "role_worker": "Механик",
        "tip_admin": "Управляйте сервисом через ⚙️ Админ панель.",
        "tip_worker": "Отправьте описание ремонта — текстом или голосом.",
        "setup_tip": "💡 *Совет:* Укажите цены на работы в разделе ⚙️ Админ панель.",
        # Shop creation
        "shop_created": (
            "✅ Сервис создан!\n\n"
            "🏪 Название: *{name}*\n🔑 Код: `{slug}`\n\n"
            "📎 Пригласительная ссылка:\n`{link}`\n\nОтправьте её механикам."
        ),
        "shop_error": "⚠️ Не удалось создать сервис. Попробуйте ещё раз.",
        "service_unavailable": "⚠️ Сервис временно недоступен. Попробуйте позже.",
        # Subscription
        "trial_expired": (
            "⏰ *Пробный период истёк*\n\n"
            "Для продолжения работы оплатите подписку:\n"
            "💰 *5 000 ₸ / месяц*"
        ),
        "subscription_inactive": (
            "🔒 *Подписка неактивна*\n\n"
            "Оплатите подписку для продолжения работы:\n"
            "💰 *5 000 ₸ / месяц*"
        ),
        "payment_instructions": (
            "💳 *Оплата через Kaspi*\n\n"
            "Переведите *5 000 ₸* на номер:\n"
            "📱 `{phone}`\n\n"
            "В комментарии укажите: `{slug}`\n\n"
            "После оплаты нажмите «✅ Я оплатил»"
        ),
        "payment_pending": "⏳ Платёж на проверке. Активируем в течение нескольких минут.",
        "payment_confirmed": "✅ Подписка активирована на 30 дней! Приятной работы 🚀",
        # Worker
        "no_shop": "❗ Вы не привязаны к сервису. Используйте пригласительную ссылку.",
        "processing": "⏳ Обрабатываю...",
        "estimate_ready": "📋 *Предварительная смета:*\n\n{text}",
        "estimate_confirmed": "✅ Смета подтверждена! Генерирую PDF...",
        "estimate_cancelled": "❌ Смета отменена.",
        "voice_error": "⚠️ Не удалось распознать голос. Попробуйте ещё раз.",
        "ai_error": "⚠️ Ошибка обработки. Попробуйте снова.",
        "price_learned": "💾 Цена сохранена: {name} — {price} ₸",
        # Buttons
        "btn_new_estimate": "🔧 Новая смета",
        "btn_admin_panel": "⚙️ Админ панель",
        "btn_pay": "💳 Оплатить 5 000 ₸",
        "btn_paid": "✅ Я оплатил",
        "btn_confirm_pdf": "✅ Подтвердить и PDF",
        "btn_cancel_estimate": "🗑 Отмена",
        "btn_cancel": "❌ Отмена",
    },
    "kz": {
        # Language picker
        "choose_language": "🌐 Интерфейс тілін таңдаңыз:",
        "btn_ru": "🇷🇺 Русский",
        "btn_kz": "🇰🇿 Қазақша",
        "btn_uz": "🇺🇿 O'zbekcha",
        "btn_kg": "🇰🇬 Кыргызча",
        "language_set_ru": "✅ Тіл орнатылды: Русский",
        "language_set_kz": "✅ Тіл орнатылды: Қазақша",
        "language_set_uz": "✅ Тіл орнатылды: O'zbekcha",
        "language_set_kg": "✅ Тіл орнатылды: Кыргызча",
        "country_set_kz": "🇰🇿 Ел: Қазақстан | Валюта: KZT ₸\nТілді таңдаңыз:",
        "country_set_uz": "🇺🇿 Ел: Өзбекстан | Валюта: UZS сум\nТілді таңдаңыз:",
        "country_set_kg": "🇰🇬 Ел: Қырғызстан | Валюта: KGS сом\nТілді таңдаңыз:",
        "choose_country": "🌍 Елді және валютаны таңдаңыз:",
        # Start
        "welcome_no_shop": (
            "👋 *AutoPilot Pro* қош келдіңіз!\n\n"
            "Автосервиске қосылу үшін шақыру сілтемесін пайдаланыңыз "
            "немесе /newshop командасымен өз сервисіңізді жасаңыз"
        ),
        "greeting": "👋 Сәлем, *{name}*!\n\n🏪 Сервис: *{shop}*\n👤 Рөл: _{role}_\n\n{tip}",
        "role_admin": "Әкімші",
        "role_worker": "Механик",
        "tip_admin": "Сервисті ⚙️ Админ панель арқылы басқарыңыз.",
        "tip_worker": "Жөндеу сипаттамасын жіберіңіз — мәтін немесе дауыс.",
        "setup_tip": "💡 *Кеңес:* ⚙️ Админ панель бөлімінде жұмыс бағаларын көрсетіңіз.",
        # Shop creation
        "shop_created": (
            "✅ Сервис жасалды!\n\n"
            "🏪 Атауы: *{name}*\n🔑 Код: `{slug}`\n\n"
            "📎 Шақыру сілтемесі:\n`{link}`\n\nМеханиктерге жіберіңіз."
        ),
        "shop_error": "⚠️ Сервис жасалмады. Қайталап көріңіз.",
        "service_unavailable": "⚠️ Сервис уақытша қолжетімсіз. Кейінірек көріңіз.",
        # Subscription
        "trial_expired": (
            "⏰ *Сынақ мерзімі аяқталды*\n\n"
            "Жалғастыру үшін жазылымды төлеңіз:\n"
            "💰 *5 000 ₸ / ай*"
        ),
        "subscription_inactive": (
            "🔒 *Жазылым белсенді емес*\n\n"
            "Жұмысты жалғастыру үшін жазылымды төлеңіз:\n"
            "💰 *5 000 ₸ / ай*"
        ),
        "payment_instructions": (
            "💳 *Kaspi арқылы төлем*\n\n"
            "Нөмірге *5 000 ₸* аударыңыз:\n"
            "📱 `{phone}`\n\n"
            "Түсініктемеге жазыңыз: `{slug}`\n\n"
            "Төлегеннен кейін «✅ Төледім» басыңыз"
        ),
        "payment_pending": "⏳ Төлем тексерілуде. Бірнеше минут ішінде белсендіреміз.",
        "payment_confirmed": "✅ Жазылым 30 күнге белсендірілді! Жақсы жұмыс 🚀",
        # Worker
        "no_shop": "❗ Сервиске тіркелмегенсіз. Шақыру сілтемесін пайдаланыңыз.",
        "processing": "⏳ Өңдеуде...",
        "estimate_ready": "📋 *Алдын ала смета:*\n\n{text}",
        "estimate_confirmed": "✅ Смета расталды! PDF дайындауда...",
        "estimate_cancelled": "❌ Смета болдырылмады.",
        "voice_error": "⚠️ Дауысты тану мүмкін болмады. Қайталаңыз.",
        "ai_error": "⚠️ Өңдеу қатесі. Қайталап көріңіз.",
        "price_learned": "💾 Баға сақталды: {name} — {price} ₸",
        # Buttons
        "btn_new_estimate": "🔧 Жаңа смета",
        "btn_admin_panel": "⚙️ Админ панель",
        "btn_pay": "💳 5 000 ₸ төлеу",
        "btn_paid": "✅ Төледім",
        "btn_confirm_pdf": "✅ Растап PDF",
        "btn_cancel_estimate": "🗑 Болдырмау",
        "btn_cancel": "❌ Болдырмау",
    },
    "uz": {
        # Language picker
        "choose_language": "🌐 Interfeys tilini tanlang:",
        "btn_ru": "🇷🇺 Русский",
        "btn_kz": "🇰🇿 Қазақша",
        "btn_uz": "🇺🇿 O'zbekcha",
        "btn_kg": "🇰🇬 Кыргызча",
        "language_set_ru": "✅ Til o'rnatildi: Русский",
        "language_set_kz": "✅ Til o'rnatildi: Қазақша",
        "language_set_uz": "✅ Til o'rnatildi: O'zbekcha",
        "language_set_kg": "✅ Til o'rnatildi: Кыргызча",
        "country_set_kz": "🇰🇿 Mamlakat: Qozog'iston | Valyuta: KZT ₸\nTilni tanlang:",
        "country_set_uz": "🇺🇿 Mamlakat: O'zbekiston | Valyuta: UZS so'm\nTilni tanlang:",
        "country_set_kg": "🇰🇬 Mamlakat: Qirg'iziston | Valyuta: KGS som\nTilni tanlang:",
        "choose_country": "🌍 Mamlakat va valyutani tanlang:",
        # Start
        "welcome_no_shop": (
            "👋 *AutoPilot Pro*ga xush kelibsiz!\n\n"
            "Avtoservisga ulashish uchun taklif havolasidan foydalaning "
            "yoki /newshop buyrug'i bilan o'z servisingizni yarating"
        ),
        "greeting": "👋 Salom, *{name}*!\n\n🏪 Servis: *{shop}*\n👤 Rol: _{role}_\n\n{tip}",
        "role_admin": "Administrator",
        "role_worker": "Mexanik",
        "tip_admin": "Servisni ⚙️ Admin panel orqali boshqaring.",
        "tip_worker": "Ta'mirlash tavsifini yuboring — matn yoki ovoz.",
        "setup_tip": "💡 *Maslahat:* ⚙️ Admin panel bo'limida ish narxlarini kiriting.",
        # Shop creation
        "shop_created": (
            "✅ Servis yaratildi!\n\n"
            "🏪 Nomi: *{name}*\n🔑 Kod: `{slug}`\n\n"
            "📎 Taklif havolasi:\n`{link}`\n\nMexaniklarga yuboring."
        ),
        "shop_error": "⚠️ Servis yaratib bo'lmadi. Qaytadan urinib ko'ring.",
        "service_unavailable": "⚠️ Servis vaqtincha mavjud emas. Keyinroq urinib ko'ring.",
        # Subscription
        "trial_expired": (
            "⏰ *Sinov muddati tugadi*\n\n"
            "Davom etish uchun obunani to'lang:\n"
            "💰 *5 000 ₸ / oy*"
        ),
        "subscription_inactive": (
            "🔒 *Obuna faol emas*\n\n"
            "Ishlashni davom ettirish uchun obunani to'lang:\n"
            "💰 *5 000 ₸ / oy*"
        ),
        "payment_instructions": (
            "💳 *Kaspi orqali to'lov*\n\n"
            "Raqamga *5 000 ₸* o'tkazing:\n"
            "📱 `{phone}`\n\n"
            "Izohda yozing: `{slug}`\n\n"
            "To'lovdan so'ng «✅ To'ladim» tugmasini bosing"
        ),
        "payment_pending": "⏳ To'lov tekshirilmoqda. Bir necha daqiqada faollashtirамиз.",
        "payment_confirmed": "✅ Obuna 30 kunga faollashtirildi! Yaxshi ish 🚀",
        # Worker
        "no_shop": "❗ Siz servisga bog'lanmagan. Taklif havolasidan foydalaning.",
        "processing": "⏳ Ishlanmoqda...",
        "estimate_ready": "📋 *Dastlabki smeta:*\n\n{text}",
        "estimate_confirmed": "✅ Smeta tasdiqlandi! PDF tayyorlanmoqda...",
        "estimate_cancelled": "❌ Smeta bekor qilindi.",
        "voice_error": "⚠️ Ovozni tanib bo'lmadi. Qaytadan urinib ko'ring.",
        "ai_error": "⚠️ Qayta ishlash xatosi. Qaytadan urinib ko'ring.",
        "price_learned": "💾 Narx saqlandi: {name} — {price} ₸",
        # Buttons
        "btn_new_estimate": "🔧 Yangi smeta",
        "btn_admin_panel": "⚙️ Admin panel",
        "btn_pay": "💳 5 000 ₸ to'lash",
        "btn_paid": "✅ To'ladim",
        "btn_confirm_pdf": "✅ Tasdiqlash va PDF",
        "btn_cancel_estimate": "🗑 Bekor qilish",
        "btn_cancel": "❌ Bekor qilish",
    },
    "kg": {
        # Language picker
        "choose_language": "🌐 Интерфейс тилин тандаңыз:",
        "btn_ru": "🇷🇺 Орусча",
        "btn_kz": "🇰🇿 Қазақша",
        "btn_uz": "🇺🇿 O'zbekcha",
        "btn_kg": "🇰🇬 Кыргызча",
        "language_set_ru": "✅ Тил коюлду: Орусча",
        "language_set_kz": "✅ Тил коюлду: Қазақша",
        "language_set_uz": "✅ Тил коюлду: O'zbekcha",
        "language_set_kg": "✅ Тил коюлду: Кыргызча",
        "country_set_kz": "🇰🇿 Өлкө: Казакстан | Валюта: KZT ₸\nТилди тандаңыз:",
        "country_set_uz": "🇺🇿 Өлкө: Өзбекстан | Валюта: UZS сом\nТилди тандаңыз:",
        "country_set_kg": "🇰🇬 Өлкө: Кыргызстан | Валюта: KGS сом\nТилди тандаңыз:",
        "choose_country": "🌍 Өлкөнү жана валютаны тандаңыз:",
        # Start
        "welcome_no_shop": (
            "👋 *AutoPilot Pro*го кош келиңиз!\n\n"
            "Авто сервиске кошулуу үчүн чакыруу шилтемесин колдонуңуз "
            "же /newshop буйругу менен өз сервисиңизди түзүңүз"
        ),
        "greeting": "👋 Саламатсызбы, *{name}*!\n\n🏪 Сервис: *{shop}*\n👤 Роль: _{role}_\n\n{tip}",
        "role_admin": "Администратор",
        "role_worker": "Механик",
        "tip_admin": "Сервисти ⚙️ Админ панель аркылуу башкарыңыз.",
        "tip_worker": "Оңдоо сүрөттөмөсүн жіберіңіз — текст же үн.",
        "setup_tip": "💡 *Кеңеш:* ⚙️ Админ панель бөлүмүндө жумуш баасын көрсөтүңүз.",
        # Shop creation
        "shop_created": (
            "✅ Сервис түзүлдү!\n\n"
            "🏪 Аты: *{name}*\n🔑 Код: `{slug}`\n\n"
            "📎 Чакыруу шилтемеси:\n`{link}`\n\nМеханиктерге жіберіңіз."
        ),
        "shop_error": "⚠️ Сервис түзүлгөн жок. Кайра аракет кылыңыз.",
        "service_unavailable": "⚠️ Сервис убактылуу жеткиликсиз. Кийинчерээк аракет кылыңыз.",
        # Subscription
        "trial_expired": (
            "⏰ *Сыноо мезгили бүттү*\n\n"
            "Улантуу үчүн жазылымды төлөңүз:\n"
            "💰 *5 000 сом / ай*"
        ),
        "subscription_inactive": (
            "🔒 *Жазылым активдүү эмес*\n\n"
            "Иштөөнү улантуу үчүн жазылымды төлөңүз:\n"
            "💰 *5 000 сом / ай*"
        ),
        "payment_instructions": (
            "💳 *Төлөм*\n\n"
            "Номерге *5 000 сом* которуңуз:\n"
            "📱 `{phone}`\n\n"
            "Комментарийде жазыңыз: `{slug}`\n\n"
            "Төлөгөндөн кийин «✅ Төлөдүм» басыңыз"
        ),
        "payment_pending": "⏳ Төлөм текшерилүүдө. Бир нече мүнөттөн кийин активдештиребиз.",
        "payment_confirmed": "✅ Жазылым 30 күнгө активдештирилди! Жакшы иш 🚀",
        # Worker
        "no_shop": "❗ Сервиске байланбадыңыз. Чакыруу шилтемесин колдонуңуз.",
        "processing": "⏳ Иштетилүүдө...",
        "estimate_ready": "📋 *Алдын ала смета:*\n\n{text}",
        "estimate_confirmed": "✅ Смета ырасталды! PDF даярдалууда...",
        "estimate_cancelled": "❌ Смета жокко чыгарылды.",
        "voice_error": "⚠️ Үндү таанып болгон жок. Кайра аракет кылыңыз.",
        "ai_error": "⚠️ Иштетүү катасы. Кайра аракет кылыңыз.",
        "price_learned": "💾 Баа сакталды: {name} — {price} сом",
        # Buttons
        "btn_new_estimate": "🔧 Жаңы смета",
        "btn_admin_panel": "⚙️ Админ панель",
        "btn_pay": "💳 5 000 сом төлөө",
        "btn_paid": "✅ Төлөдүм",
        "btn_confirm_pdf": "✅ Ырастап PDF",
        "btn_cancel_estimate": "🗑 Жокко чыгаруу",
        "btn_cancel": "❌ Жокко чыгаруу",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    lang = lang if lang in TEXTS else "ru"
    text = TEXTS[lang].get(key) or TEXTS["ru"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
