# tutor/config.py
#
# Die Einstellungen des Tutors — seine eigenen, nicht mehr die von ZENTRALE.
#
# Seit 2026-10-09 (eigenes Repo, eigener Prozess) liest der Tutor nichts mehr
# aus ZENTRALEs ai_config. Was vorher dort stand (tutor_optik, whisper_url,
# tts_url, default_lang, tutor_presence_react), steht jetzt hier.
#
# ── Woher ein Wert kommt (erste Quelle gewinnt) ─────────────────────────
#   Laufzeit-Wechsel (set_override)  >  Env TUTOR_<NAME>
#   >  ~/.config/language-tutor/einstellungen.json
#   >  <daten>/tutor_config.json (die alte Datei: provider/model/native)
#   >  Standard unten.
#
# KEINE Schlüssel hier. Die liegen in einer eigenen Datei
# (tutor/modell/schluessel.py), damit diese Datei gefahrlos gezeigt und
# kopiert werden kann.

import json
import os

from . import pfade

# Alle Einstellungen mit Standardwert — eine Liste, damit niemand raten muss.
STANDARD = {
    # Modell
    "ziel":              "direkt",   # direkt = eigener Schlüssel | hub = Sashas Server (noch nicht da)
    "provider":          None,       # None → das Sprachprofil entscheidet
    "model":             None,
    "history_window":    30,
    "max_tokens":        None,       # None → je Anbieter-Art (anbieter.py)
    "temperature":       0.4,
    "effort":            "low",
    "monatsbudget_euro": 5.0,        # Deckel für Cloud-Kosten des Tutors je Monat
    "hub_url":           "",         # später: Sashas Server (ziel = hub)
    "ollama_url":        "http://localhost:11434",
    "ollama_model":      "qwen3.5:9b",
    # Lernen
    "native":            "en",       # Muttersprache (Glosse auf Karten)
    # Zimmer, Stimme
    "tutor_optik":       "pixel",    # pixel | alt
    "whisper_url":       "http://localhost:5050",
    "tts_url":           "http://localhost:5051",
    "default_lang":      "de",
    "presence_react":    "1",        # 0 = auf „jemand ist da" nicht reagieren
    # Server
    "host":              "127.0.0.1",
    "port":              5070,
}

_overrides = {}   # Laufzeit-Wechsel (aus dem Zimmer, ohne Neustart)


def _lesen(pfad: str) -> dict:
    if not os.path.exists(pfad):
        return {}
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        print(f"[tutor.config] {pfad} konnte nicht gelesen werden: {e}")
        return {}


def _alte_datei() -> str:
    return os.path.join(pfade.daten_ordner(), "tutor_config.json")


def setting(name: str, default=None):
    """Wert einer Einstellung (Reihenfolge siehe Kopf). default=None → der
    Standard aus STANDARD."""
    if default is None:
        default = STANDARD.get(name)
    if name in _overrides:
        return _overrides[name]
    env = os.environ.get("TUTOR_" + name.upper())
    if env not in (None, ""):
        return env
    for quelle in (_lesen(pfade.einstellungen_datei()), _lesen(_alte_datei())):
        val = quelle.get(name)
        if val not in (None, ""):
            return val
    return default


def set_override(name: str, value, persist: bool = False):
    """Setzt eine Einstellung zur Laufzeit. Leerer Wert löscht den Wechsel.
    persist=True schreibt sie zusätzlich in einstellungen.json."""
    if value in (None, ""):
        _overrides.pop(name, None)
    else:
        _overrides[name] = value
    if persist:
        _speichern(name, value)


def _speichern(name: str, value):
    pfad = pfade.einstellungen_datei()
    daten = _lesen(pfad)
    if value in (None, ""):
        daten.pop(name, None)
    else:
        daten[name] = value
    try:
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        tmp = pfad + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=2, ensure_ascii=False)
        os.replace(tmp, pfad)
    except Exception as e:
        print(f"[tutor.config] Speichern fehlgeschlagen: {e}")
