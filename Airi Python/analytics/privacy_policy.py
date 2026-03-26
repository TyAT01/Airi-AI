from typing import Optional

# localeRemap logic would go here if we had the full i18n module
locale_remap = {
    "en-US": "en",
    "ja-JP": "ja",
    "zh-CN": "zh-Hans",
}

supported_privacy_policy_locales = {"en", "ja", "zh-Hans"}

def get_analytics_privacy_policy_url(locale: Optional[str] = None) -> str:
    normalized_locale = locale_remap.get(locale or "en", locale or "en")
    docs_locale = normalized_locale if normalized_locale in supported_privacy_policy_locales else "en"
    return f"https://airi.moeru.ai/docs/{docs_locale}/about/privacy"
