# tutor/pfade.py
#
# Wo der Tutor seine Sachen hat: Daten (Lernstände), Einstellungen, Schlüssel.
#
# Seit 2026-10-09 ist der Tutor ein eigenes Programm (eigenes Repo, eigener
# Prozess, erste App nach dem Hub-Bauplan von ZENTRALE). Vorher lag alles unter
# ZENTRALE/tutor/data — und dort liegen Sashas Lernstände heute noch. Damit
# nichts verschoben werden muss, sucht der Tutor seine Daten in dieser
# Reihenfolge:
#
#   1. Env TUTOR_DATEN_ORDNER                    (Tests, Experimente)
#   2. Einstellung daten_ordner in einstellungen.json
#   3. <repo>/tutor/data, wenn dort schon Lernstände liegen
#   4. der alte Ort ../ZENTRALE/tutor/data neben diesem Repo (Umzugshilfe)
#   5. sonst <repo>/tutor/data (frische Installation)
#
# Einstellungen und Schlüssel liegen NICHT im Repo, sondern im Konfig-Ordner
# (~/.config/language-tutor, Env TUTOR_KONFIG_ORDNER). So kann kein vergessener
# .gitignore-Eintrag einen Schlüssel ins Repo bringen.

import json
import os

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EIGENE_DATEN = os.path.join(WURZEL, "tutor", "data")
_ALTER_ORT = os.path.normpath(os.path.join(WURZEL, "..", "ZENTRALE", "tutor", "data"))


def konfig_ordner() -> str:
    return os.path.expanduser(os.environ.get("TUTOR_KONFIG_ORDNER")
                              or "~/.config/language-tutor")


def einstellungen_datei() -> str:
    return os.path.join(konfig_ordner(), "einstellungen.json")


def _hat_lernstaende(ordner: str) -> bool:
    return (os.path.isdir(os.path.join(ordner, "staende"))
            or os.path.exists(os.path.join(ordner, "aktiver_stand")))


def _aus_einstellungen() -> str:
    try:
        with open(einstellungen_datei(), encoding="utf-8") as f:
            return str((json.load(f) or {}).get("daten_ordner") or "")
    except (OSError, ValueError):
        return ""


def daten_ordner() -> str:
    """Der Ordner mit den Lernständen (siehe Kopf)."""
    gesetzt = os.environ.get("TUTOR_DATEN_ORDNER") or _aus_einstellungen()
    if gesetzt:
        return os.path.abspath(os.path.expanduser(gesetzt))
    if _hat_lernstaende(_EIGENE_DATEN):
        return _EIGENE_DATEN
    if _hat_lernstaende(_ALTER_ORT):
        return _ALTER_ORT
    return _EIGENE_DATEN


def ist_alter_ort(ordner: str = None) -> bool:
    """Liest der Tutor noch aus dem alten ZENTRALE-Ordner? (für den Hinweis
    beim Start, damit Sasha weiß, dass ein Umzug noch aussteht)"""
    return os.path.abspath(ordner or daten_ordner()) == _ALTER_ORT
