import json
from pathlib import Path

TRANSLATIONS_CACHE = Path(__file__).resolve().parent / "data" / "translations_cache.json"

def _load_cache():
    if TRANSLATIONS_CACHE.exists():
        return json.loads(TRANSLATIONS_CACHE.read_text(encoding="utf-8"))
    return {}

def _save_cache(cache):
    TRANSLATIONS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATIONS_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

def t(text, lang="fr"):
    """
    Translate text to target language.
    - If lang is 'fr', return text as-is (French is the base language).
    - If lang is 'en' (or other), auto-translate and cache the result.
    """
    if lang == "fr" or not text or not text.strip():
        return text

    cache = _load_cache()

    # Check cache first
    cache_key = f"{lang}::{text}"
    if cache_key in cache:
        return cache[cache_key]

    # Translate
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="fr", target=lang).translate(text)
    except Exception:
        return text  # Fallback: return original if translation fails

    # Save to cache
    cache[cache_key] = translated
    _save_cache(cache)

    return translated