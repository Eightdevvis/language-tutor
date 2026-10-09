# tutor/modell/schleife.py
#
# Die Werkzeug-Schleife des Tutors: Modell fragen → will es Werkzeuge? →
# ausführen → Ergebnisse zurück → nächste Runde, bis es antwortet.
#
# Portiert aus ZENTRALE core/werkzeug_schleife.py (2026-10-09), aber nur der
# Teil, den der Tutor nutzte (dort „tutor_mode"): kein Erlaubnis-Gate, keine
# terminalen Kern-Werkzeuge, keine Bild-Marker, kein Speichern ins Gedächtnis
# des Assistenten. Die Antwort geht roh raus.
#
# Ein Weg (weg_*.py) ist ein Adapter mit drei Dingen:
#   runde()                     Generator: EIN Modell-Aufruf, `return Runde(...)`
#   assistent_anhaengen(runde)  den Zug des Modells in seinem Format anhängen
#   ergebnisse_anhaengen(liste) [(call_id, text, is_error)] in seinem Format
#
# Fehler gehen als Event {"fehler": text} raus, NIE als Antworttext — sonst
# läse die nächste Runde die Fehlermeldung als eigene Aussage.

from dataclasses import dataclass, field

MAX_RUNDEN = 6


@dataclass
class Runde:
    text: str
    calls: list = field(default_factory=list)   # [(call_id, name, args)]
    roh: object = None


class Abbruch(Exception):
    """Der Weg bricht mit einer Meldung ab (z. B. Anbieter lehnt ab)."""


def fehler(text: str) -> dict:
    return {"fehler": text}


def laufen(adapter, *, ausfuehren, name: str = "Cloud"):
    """Der ganze Zug. Yieldet Text-Tokens und Events (reflect, werkzeug,
    fehler)."""
    for _ in range(MAX_RUNDEN):
        try:
            runde = yield from adapter.runde()
        except Abbruch as e:
            yield fehler(str(e))
            return
        except Exception as e:                       # noqa: BLE001
            yield fehler(f"{name}-Fehler: {e}")
            return
        if not runde.calls:
            if runde.text:
                yield runde.text
            return
        adapter.assistent_anhaengen(runde)
        ergebnisse = []
        for call_id, wname, args in runde.calls:
            yield {"werkzeug": {"phase": "start", "name": wname, "args": args}}
            if ausfuehren is None:
                ergebnisse.append((call_id, f"Werkzeug '{wname}' gibt es hier nicht.", True))
                continue
            try:
                text = ausfuehren(wname, args)
                ergebnisse.append((call_id, str(text), False))
            except Exception as e:                   # noqa: BLE001
                yield {"werkzeug": {"phase": "fehler", "name": wname, "text": str(e)}}
                ergebnisse.append((call_id, f"Werkzeug '{wname}' ist fehlgeschlagen: {e}", True))
        adapter.ergebnisse_anhaengen(ergebnisse)
    yield fehler(f"Maximale Werkzeug-Tiefe erreicht ({MAX_RUNDEN} Runden).")
