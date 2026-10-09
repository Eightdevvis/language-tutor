# tutor/modell/schluessel.py
#
# Der eigene Schlüssel des Tutors (seit 2026-10-09).
#
# Vorher lieh sich der Tutor die Schlüssel von ZENTRALE (die standen nach dem
# Start in os.environ). Jetzt hat er seine eigene Datei, außerhalb des Repos:
#
#   ~/.config/language-tutor/schluessel      (Env TUTOR_SCHLUESSEL_DATEI)
#
# Eine Zeile je Anbieter, Name wie in anbieter_liste.py:
#   claude = sk-ant-…
#   qwen   = sk-…
# Leerzeilen und Zeilen mit # werden übersprungen.
#
# Die Datei darf nur für Sasha lesbar sein (Rechte 600). Ist sie für andere
# lesbar, nimmt der Tutor sie NICHT — lieber eine klare Meldung als ein
# Schlüssel, den jeder auf dem Rechner mitlesen kann.
#
# Bewusst KEIN Rückgriff auf Umgebungsvariablen wie ANTHROPIC_API_KEY: sonst
# zahlt der Tutor still mit einem fremden Schlüssel (z. B. dem von ZENTRALE),
# und sein Budget zählt nichts mehr. Später (verkauft) liegt beim Kunden gar
# kein Schlüssel — dann fährt die Leitung über den Hub (hub.py).

import os
import stat

from .. import pfade


def datei() -> str:
    return os.path.expanduser(os.environ.get("TUTOR_SCHLUESSEL_DATEI")
                              or os.path.join(pfade.konfig_ordner(), "schluessel"))


class SchluesselProblem(Exception):
    """Die Datei ist da, taugt aber nicht (z. B. für andere lesbar)."""


def _lesen() -> dict:
    pfad = datei()
    try:
        st = os.stat(pfad)
    except OSError:
        return {}
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise SchluesselProblem(
            "Die Schlüssel-Datei ist für andere auf diesem Rechner lesbar. "
            "Stell ihre Rechte so ein, dass nur du sie lesen darfst — "
            "dann nimmt der Tutor sie.")
    raus = {}
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if not zeile or zeile.startswith("#") or "=" not in zeile:
                continue
            name, wert = zeile.split("=", 1)
            if name.strip() and wert.strip():
                raus[name.strip().lower()] = wert.strip()
    return raus


def holen(anbieter: str):
    """Der Schlüssel für diesen Anbieter oder None. Wirft SchluesselProblem,
    wenn die Datei unsicher ist."""
    return _lesen().get((anbieter or "").lower())


def hat(anbieter: str) -> bool:
    try:
        return bool(holen(anbieter))
    except (SchluesselProblem, OSError):
        return False


def problem() -> str:
    """Klartext, wenn mit der Datei etwas nicht stimmt — sonst ''."""
    try:
        _lesen()
        return ""
    except SchluesselProblem as e:
        return str(e)
    except OSError as e:
        return f"Schlüssel-Datei nicht lesbar: {e}"
