import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("airi_i18n")

class I18nManager:
    def __init__(self, default_locale: str = "en"):
        self.locales: Dict[str, Dict[str, str]] = {
            "en": {
                "base.prompt.prefix": "Hello, I am AIRI.",
                "base.prompt.suffix": "How can I help you today?"
            }
        }
        self.current_locale = default_locale

    def load_locale(self, locale: str, data: Dict[str, str]):
        self.locales[locale] = data

    def translate(self, key: str, **kwargs) -> str:
        text = self.locales.get(self.current_locale, {}).get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text

    def set_locale(self, locale: str):
        if locale in self.locales:
            self.current_locale = locale
            logger.info(f"Locale set to: {locale}")
        else:
            logger.warning(f"Locale not found: {locale}")
