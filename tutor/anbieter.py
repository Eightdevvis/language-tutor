# tutor/anbieter.py
#
# Die Naht des Tutors zu seiner Modell-Leitung (tutor/modell/).
#
# Bis 2026-10-08 hatte der Tutor eigene Cloud-Schleifen, vom 08.10. bis 09.10.
# fuhr er auf der Straße von ZENTRALE (kern.fahren). Seit 2026-10-09 ist er ein
# eigenes Programm und fährt auf seiner eigenen kleinen Leitung — mit eigenem
# Schlüssel und eigenem Budget. Die Aufrufer (session, memory) sehen davon
# nichts: dieses Modul behält seine Schnittstelle.
#
# Einstellungen (tutor/config.py, Env TUTOR_<NAME>):
#   max_tokens   harter Deckel je Antwort. Standard je Art: OpenAI-kompatibel
#                140 (gegen echtes qwen gemessen, docs/tutor_persona_tuning.md),
#                Anthropic 2000 (Denken zählt mit). Ein Wert im Sprachprofil
#                (max_tokens) geht vor.
#   temperature  0.4 (nur OpenAI-kompatibel)
#   effort       'low' (nur Anthropic)

from . import config
from .modell import anbieter_liste, leitung, schluessel

LOKAL = anbieter_liste.LOKAL

_MAX_TOKENS_JE_ART = {"openai_compat": 140, "anthropic": 2000}


def eintrag(name: str) -> dict:
    """Anbieter-Eintrag; unbekannt → der lokale. 'kind' bleibt als Name für
    die Art erhalten (session.backend_kind fragt danach)."""
    e = dict(anbieter_liste.eintrag(name) or anbieter_liste.eintrag(LOKAL))
    e["kind"] = e.get("art")
    return e


def bekannt(name: str) -> bool:
    return bool(anbieter_liste.eintrag(name))


def trains_on_data(name: str) -> bool:
    return anbieter_liste.trains_on_data(name)


def default_model(name: str):
    return eintrag(name).get("default_model")


def waehlbar(name: str) -> bool:
    """Kann der Tutor diesen Anbieter jetzt nehmen? Lokal immer; Cloud nur mit
    eigenem Schlüssel."""
    if eintrag(name).get("art") == "ollama":
        return True
    return schluessel.hat(name)


def liste() -> list:
    """Alle Anbieter fürs Zimmer (Einstellungen)."""
    return [{"name": n, "default_model": e.get("default_model"),
             "trains_on_data": anbieter_liste.trains_on_data(n),
             "jurisdiction": e.get("jurisdiction"), "enabled": waehlbar(n)}
            for n, e in anbieter_liste.alle().items()]


def _zahl(name, standard, art=float):
    try:
        v = config.setting(name, None)
        return art(v) if v not in (None, "") else standard
    except (TypeError, ValueError):
        return standard


def fahren(anbieter: str, modell, verlauf: list, *, system: str, tools: list,
           tool_executor, max_tokens: int = None):
    """Einen Tutor-Zug fahren. Generator: Text-Tokens + dicts (werkzeug,
    reflect, fehler) — der Aufrufer filtert."""
    if not bekannt(anbieter):
        anbieter = LOKAL
    art = anbieter_liste.eintrag(anbieter).get("art")
    # Reihenfolge wie vorher: Sprachprofil > Einstellung > Standard je Art.
    deckel = max_tokens or _zahl("max_tokens", None, int) or _MAX_TOKENS_JE_ART.get(art)
    yield from leitung.fahren(
        anbieter, modell, verlauf, system=system, tools=tools,
        ausfuehren=tool_executor, max_tokens=deckel,
        temperatur=_zahl("temperature", 0.4),
        effort=str(config.setting("effort") or "low"))
