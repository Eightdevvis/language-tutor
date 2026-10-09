# tutor/modell/kosten.py
#
# Was der Tutor kostet — eigene Buchung, eigenes Monatsbudget (seit 2026-10-09).
#
# Vorher buchte der Tutor in ZENTRALEs Kostenbuch (data/ai_usage.json), und
# Lucías Gespräche liefen über den Budget-Deckel des Assistenten. Jetzt zählt
# der Tutor selbst: jeder Cloud-Aufruf wird hier gebucht, und ist das
# Monatsbudget (Einstellung monatsbudget_euro) erreicht, fährt die Leitung
# nicht mehr in die Cloud, sondern sagt es klar.
#
# Ablage: <daten>/kosten/<rechner>.json — eine Datei pro Rechner, weil die
# Daten zwischen Sashas Rechnern abgeglichen werden („neueste Datei gewinnt"):
# zwei Rechner, die in DIESELBE Datei buchen, würden sich gegenseitig
# überschreiben. Für das Budget werden alle Dateien zusammengezählt.
#
# Preise (USD je 1 Mio. Token) aus ZENTRALE core/prices.py, Stand 2026-08-15.
# Unbekanntes Modell → teuer geschätzt (lieber zu hoch als zu niedrig).

import json
import os
import socket
import threading
import time

from .. import config, pfade

PREISE = {
    "claude-opus-5":     {"in": 5.00, "out": 25.00, "cache_read": 0.10, "cache_write": 2.00},
    "claude-sonnet-5":   {"in": 3.00, "out": 15.00, "cache_read": 0.10, "cache_write": 2.00},
    "claude-sonnet-4-6": {"in": 3.00, "out": 15.00, "cache_read": 0.10, "cache_write": 2.00},
    "claude-haiku-4-5":  {"in": 1.00, "out":  5.00, "cache_read": 0.10, "cache_write": 2.00},
    "qwen-plus":         {"in": 0.40, "out": 1.20},
    "qwen-turbo":        {"in": 0.05, "out": 0.20},
    "qwen-max":          {"in": 1.60, "out": 6.40},
    "gpt-4o":            {"in": 2.50, "out": 10.00},
    "gpt-4o-mini":       {"in": 0.15, "out": 0.60},
    "grok-4":            {"in": 3.00, "out": 15.00},
    "gemini-2.5-pro":    {"in": 1.25, "out": 10.00},
    "gemini-2.5-flash":  {"in": 0.30, "out": 2.50},
    "deepseek-chat":     {"in": 0.27, "out": 1.10},
    "llama-3.3-70b-versatile": {"in": 0.59, "out": 0.79},
    "mistral-large-latest":    {"in": 2.00, "out": 6.00},
}
UNBEKANNT = {"in": 5.00, "out": 25.00, "cache_read": 0.10, "cache_write": 2.00}
USD_EUR = 0.92

_lock = threading.Lock()


def euro(modell: str, *, rein: int = 0, raus: int = 0,
         cache_lesen: int = 0, cache_schreiben: int = 0) -> float:
    p = PREISE.get(modell or "") or UNBEKANNT
    je_rein = p["in"] / 1_000_000
    usd = (rein * je_rein
           + cache_lesen * je_rein * p.get("cache_read", 1.0)
           + cache_schreiben * je_rein * p.get("cache_write", 1.0)
           + raus * p["out"] / 1_000_000)
    return usd * USD_EUR


def _ordner() -> str:
    return os.path.join(pfade.daten_ordner(), "kosten")


def _datei() -> str:
    rechner = (socket.gethostname() or "rechner").replace(os.sep, "_")
    return os.path.join(_ordner(), rechner + ".json")


def _monat() -> str:
    return time.strftime("%Y-%m")


def _lesen(pfad: str) -> dict:
    try:
        with open(pfad, encoding="utf-8") as f:
            return json.load(f) or {}
    except (OSError, ValueError):
        return {}


def buchen(modell: str, **tokens) -> float:
    """Einen Aufruf buchen; gibt die Euro dieses Aufrufs zurück."""
    betrag = euro(modell, **tokens)
    with _lock:
        pfad = _datei()
        daten = _lesen(pfad)
        m = daten.setdefault(_monat(), {"euro": 0.0, "aufrufe": 0})
        m["euro"] = round(m["euro"] + betrag, 6)
        m["aufrufe"] += 1
        try:
            os.makedirs(os.path.dirname(pfad), exist_ok=True)
            tmp = pfad + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(daten, f, indent=2)
            os.replace(tmp, pfad)
        except OSError as e:
            # Nicht still: eine verlorene Buchung macht den Deckel blind.
            print(f"[tutor.kosten] Buchung fehlgeschlagen ({modell}): {e}", flush=True)
    print(f"[tutor.kosten] {modell} ≈{betrag:.4f}€ (Monat {monat_euro():.2f}€ "
          f"von {budget():.2f}€)", flush=True)
    return betrag


def monat_euro() -> float:
    """Was der Tutor diesen Monat schon gekostet hat (alle Rechner)."""
    summe = 0.0
    try:
        namen = os.listdir(_ordner())
    except OSError:
        return 0.0
    for n in namen:
        if n.endswith(".json"):
            summe += float((_lesen(os.path.join(_ordner(), n)).get(_monat()) or {})
                           .get("euro", 0.0))
    return summe


def budget() -> float:
    try:
        return float(config.setting("monatsbudget_euro"))
    except (TypeError, ValueError):
        return 0.0


def budget_aufgebraucht() -> bool:
    return monat_euro() >= budget()
