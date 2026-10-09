# tutor/modell/anbieter_liste.py
#
# Die Anbieter, mit denen der Tutor reden kann. Abgeschrieben aus ZENTRALE
# (core/providers.py, Stand 2026-10-09) — bewusst eine Kopie, kein Import:
# eine App importiert keinen Hub-Code (hub_bauplan.md in ZENTRALE). Laufen die
# beiden Tabellen irgendwann auseinander, ist das in Ordnung: der Tutor hat
# seine eigenen Modelle und sein eigenes Budget.
#
# art:            'anthropic' | 'openai_compat' | 'ollama' — welcher Weg (weg_*.py)
# trains_on_data: False = trainiert nachweislich nicht; None/True → laut warnen

LOKAL = "local"

ANBIETER = {
    LOKAL: {
        "art": "ollama", "base_url": None, "default_model": None,
        "jurisdiction": "local", "trains_on_data": False,
    },
    "claude": {
        "art": "anthropic", "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-5", "jurisdiction": "US",
        "trains_on_data": False,
    },
    "qwen": {
        "art": "openai_compat",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus", "jurisdiction": "SG",
        "trains_on_data": False,
    },
    "openai": {
        "art": "openai_compat", "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o", "jurisdiction": "US", "trains_on_data": False,
    },
    "grok": {
        "art": "openai_compat", "base_url": "https://api.x.ai/v1",
        "default_model": "grok-4", "jurisdiction": "US", "trains_on_data": None,
    },
    "gemini": {
        "art": "openai_compat",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.5-pro", "jurisdiction": "US",
        "trains_on_data": True,
    },
    "deepseek": {
        "art": "openai_compat", "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat", "jurisdiction": "CN",
        "trains_on_data": True,
    },
    "groq": {
        "art": "openai_compat", "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile", "jurisdiction": "US",
        "trains_on_data": None,
    },
    "mistral": {
        "art": "openai_compat", "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-large-latest", "jurisdiction": "EU",
        "trains_on_data": False,
    },
}


def eintrag(name: str) -> dict:
    """Eintrag des Anbieters oder {} (unbekannt)."""
    return ANBIETER.get(name or "") or {}


def alle() -> dict:
    return dict(ANBIETER)


def ist_cloud(name: str) -> bool:
    return eintrag(name).get("art") in ("anthropic", "openai_compat")


def trains_on_data(name: str) -> bool:
    """Unbekannt/unverifiziert zählt vorsichtshalber als ja."""
    return eintrag(name).get("trains_on_data") is not False
