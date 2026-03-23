import json
import tempfile
import os
import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """Ты — опытный мастер-приёмщик автосервиса в Казахстане.
Твоя задача: из описания ремонта на русском или казахском языке извлечь структурированные данные.

ПРАВИЛА:
- НИКОГДА не задавай вопросы — всегда создавай смету
- Если информация об авто отсутствует — оставь поля пустыми (НЕ пиши "Unknown")
- Если ремонт описан расплывчато — добавь логичные подзадачи
- Отвечай ТОЛЬКО валидным JSON без markdown и пояснений
- Названия работ и запчастей пиши на РУССКОМ языке
- ВАЖНО: марку, модель и год автомобиля ВСЕГДА выноси в поле "car", НЕ включай их в название работы.
  Пример: "замена радиатора на хайландер 2003" → car: {make: Toyota, model: Highlander, year: 2003}, labor: [{name: "Замена радиатора"}]
- Используй официальные полные названия: не "камри" а "Camry", не "хайландер" а "Highlander"
- Название работы должно быть грамматически правильным: "Замена радиатора", "Регулировка клапанов", "Замена тормозных колодок"

РАСПОЗНАВАНИЕ АВТОМОБИЛЕЙ (народные названия → официальные):
- камри, camry → make: Toyota, model: Camry
- приора → make: Lada, model: Priora
- крузак, круизёр → make: Toyota, model: Land Cruiser
- прадо → make: Toyota, model: Land Cruiser Prado
- хайландер → make: Toyota, model: Highlander
- рав4, rav4 → make: Toyota, model: RAV4
- авенсис → make: Toyota, model: Avensis
- короллa, corolla → make: Toyota, model: Corolla
- виш, wish → make: Toyota, model: Wish
- мерс, мерседес → make: Mercedes-Benz
- бмв, bmw → make: BMW
- ауди → make: Audi
- нексия → make: Daewoo, model: Nexia
- матиз → make: Daewoo, model: Matiz
- кобальт → make: Chevrolet, model: Cobalt
- круз → make: Chevrolet, model: Cruze
- акцент → make: Hyundai, model: Accent
- соренто → make: Kia, model: Sorento
- спортейдж → make: Kia, model: Sportage
- туксон → make: Hyundai, model: Tucson
- тигуан → make: Volkswagen, model: Tiguan
- гольф → make: Volkswagen, model: Golf
- инфинити → make: Infiniti
- лексус → make: Lexus
- хонда → make: Honda
- ниссан → make: Nissan
- митсубиси, митсубishi → make: Mitsubishi
- субару → make: Subaru
- мазда → make: Mazda
- опель → make: Opel
- форд → make: Ford
- рено → make: Renault
- пежо → make: Peugeot
- ситроен → make: Citroën
- шевроле → make: Chevrolet
- хундай, хёндай → make: Hyundai
- киа, kia → make: Kia
- уаз → make: UAZ
- газель → make: GAZ, model: Gazelle
- жигули, ваз → make: Lada / VAZ

ФОРМАТ ОТВЕТА (строгий JSON):
{
  "car": {
    "make": "Toyota",
    "model": "Camry",
    "year": "2020",
    "vin": ""
  },
  "labor": [
    {"name": "Замена масла двигателя", "qty": 1},
    {"name": "Замена масляного фильтра", "qty": 1}
  ],
  "parts": [
    {"name": "Моторное масло 5W-40", "qty": 4, "unit": "л"},
    {"name": "Масляный фильтр", "qty": 1, "unit": "шт"}
  ],
  "notes": "..."
}

ЕДИНИЦЫ ИЗМЕРЕНИЯ: всегда на русском — "шт", "л", "кг", "компл", "м". Никогда не использовать "pcs", "liter", "set".
  ],
  "notes": "Клиент просил синтетическое масло"
}
"""


def transcribe_voice(file_bytes: bytes, filename: str = "voice.ogg") -> str:
    """Transcribe voice message using Whisper."""
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, f, "audio/ogg"),
                language="ru",
            )
        return result.text
    finally:
        os.unlink(tmp_path)


def extract_repair_data(text: str, custom_prompt: str | None = None) -> dict:
    """Extract structured repair data from free text using GPT-4o."""
    system = custom_prompt if custom_prompt else SYSTEM_PROMPT
    # OpenAI requires the word "json" in messages when using json_object mode
    if "json" not in system.lower():
        system += "\n\nОтвечай строго в формате json."
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        logger.info(f"AI response: {raw[:300]}")
        return json.loads(raw)
    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        return {
            "car": {"make": "", "model": "", "year": "", "vin": ""},
            "labor": [{"name": "Ремонт", "qty": 1}],
            "parts": [],
            "notes": text,
        }
