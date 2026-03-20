import json
import tempfile
import os
import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are an experienced auto repair shop estimator in Kazakhstan.
Your job: analyze a mechanic's description and extract structured repair data.

RULES:
- NEVER ask questions — always produce an estimate
- If car info is missing, use "Unknown"
- If a repair is vague, add the most logical sub-tasks
- Always respond in valid JSON only — no markdown, no explanation

OUTPUT FORMAT (strict JSON):
{
  "car": {
    "make": "Toyota",
    "model": "Camry",
    "year": "2020",
    "vin": ""
  },
  "labor": [
    {"name": "Oil change", "qty": 1},
    {"name": "Oil filter replacement", "qty": 1}
  ],
  "parts": [
    {"name": "Engine oil 5W-40", "qty": 4, "unit": "liter"},
    {"name": "Oil filter", "qty": 1, "unit": "pcs"}
  ],
  "notes": "Customer requested synthetic oil"
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


def extract_repair_data(text: str) -> dict:
    """Extract structured repair data from free text using GPT-4o."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        return {
            "car": {"make": "Unknown", "model": "Unknown", "year": "", "vin": ""},
            "labor": [{"name": text[:100], "qty": 1}],
            "parts": [],
            "notes": "",
        }
