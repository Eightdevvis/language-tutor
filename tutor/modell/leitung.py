# tutor/modell/leitung.py
#
# Der eine Einstieg zur Modell-Leitung des Tutors (seit 2026-10-09).
#
#   fahren(anbieter, modell, verlauf, system=, tools=, ausfuehren=, …)
#
# Zwei Ziele, per Einstellung „ziel":
#   direkt  der eigene Schlüssel (schluessel.py), eigenes Budget (kosten.py)
#   hub     später Sashas Server (hub.py) — heute eine klare Meldung
#
# Was hier reingeht, ist genau der Prompt des Tutors, sein Verlauf und seine
# Werkzeuge. Es gibt keinen Weg, „die Werkzeuge des Assistenten" oder dessen
# Gedächtnis zu bekommen: tools=None heißt hier „keine", nicht „alle".
# Genau dieses Missverständnis (tools=None = voller Assistent) hatte den
# Tutor bis 08.10. an Sashas Kalender gebracht.

from .. import config
from . import anbieter_liste, hub, kosten, schluessel, schleife
from . import weg_anthropic, weg_ollama, weg_openai


def ziel() -> str:
    z = str(config.setting("ziel") or "direkt").strip().lower()
    return z if z in ("direkt", "hub") else "direkt"


def warum_nicht(anbieter: str) -> str:
    """Klartext, warum dieser Anbieter gerade nicht fahren kann — '' = geht."""
    if ziel() == "hub":
        return hub.NOCH_NICHT
    e = anbieter_liste.eintrag(anbieter)
    if not e:
        return f"Unbekannter Anbieter „{anbieter}“."
    if e["art"] == "ollama":
        return "" if weg_ollama.erreichbar() else "Das lokale Modell (Ollama) ist nicht erreichbar."
    p = schluessel.problem()
    if p:
        return p
    if not schluessel.hat(anbieter):
        return (f"Für „{anbieter}“ liegt kein Schlüssel in der Schlüssel-Datei des "
                f"Tutors ({schluessel.datei()}).")
    if kosten.budget_aufgebraucht():
        return (f"Das Monatsbudget des Tutors ({kosten.budget():.2f} €) ist "
                f"aufgebraucht.")
    return ""


def fahren(anbieter: str, modell, verlauf: list, *, system: str, tools,
           ausfuehren, max_tokens: int = None, temperatur: float = None,
           effort: str = None):
    """Einen Zug fahren. Generator: Text-Tokens + Events (reflect, werkzeug,
    fehler)."""
    tools = list(tools or [])          # None = keine Werkzeuge, nie „alle"
    system = str(system or "")
    if ziel() == "hub":
        yield from hub.fahren(verlauf, anbieter=anbieter, modell=modell,
                              system=system, tools=tools, ausfuehren=ausfuehren)
        return
    e = anbieter_liste.eintrag(anbieter)
    if not e:
        yield schleife.fehler(f"Unbekannter Anbieter „{anbieter}“ — keine Leitung dorthin.")
        return
    if e["art"] == "ollama":
        yield from weg_ollama.fahren(verlauf, modell=modell, system=system,
                                     tools=tools, ausfuehren=ausfuehren)
        return
    grund = warum_nicht(anbieter)
    if grund:
        yield schleife.fehler(grund)
        return
    key = schluessel.holen(anbieter)
    modell = modell or e.get("default_model")
    if e["art"] == "anthropic":
        yield from weg_anthropic.fahren(
            verlauf, modell=modell, system=system, tools=tools,
            ausfuehren=ausfuehren, schluessel=key, max_tokens=max_tokens,
            effort=effort)
    else:
        yield from weg_openai.fahren(
            verlauf, modell=modell, system=system, tools=tools,
            ausfuehren=ausfuehren, schluessel=key, base_url=e["base_url"],
            max_tokens=max_tokens, temperatur=temperatur)
