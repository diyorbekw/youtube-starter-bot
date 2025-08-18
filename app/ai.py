from openai import OpenAI
from app.config import OPENAI_API_KEY
import json
import re

client = OpenAI(api_key=OPENAI_API_KEY)

def gen_seo(topic: str, lang: str = "en") -> dict:
    prompt = f"""YouTube SEO: topic: {topic}.
Language: {lang}. Return: only in JSON format: title, description (max 1500 characters), tags (10-15)."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    text = resp.choices[0].message.content.strip()

    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "title": topic[:100],
        "description": text,
        "tags": ["youtube", "video"]
    }
