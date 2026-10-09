# tutor/modell/hub.py
#
# Ziel „hub": der Weg über Sashas Server (später, wenn der Tutor verkauft wird).
#
# Dann liegt beim Kunden KEIN Schlüssel. Der Tutor schickt seinen Zug (Prompt,
# Verlauf, Werkzeug-Liste) an Sashas Server; der hält den Schlüssel, zählt pro
# Nutzer und prüft das Abo. Gedachte Schnittstelle (noch nicht gebaut):
#
#   POST <hub_url>/modell/fahren   Kopf: Authorization: Bearer <Nutzer-Zugang>
#        {anbieter, modell, system, verlauf, tools, max_tokens}
#   → Event-Strom wie hier (Text, werkzeug, fehler); Werkzeuge führt weiter der
#     Tutor beim Kunden aus.
#
# Heute: ein Platzhalter mit klarer Meldung. Wer ziel = hub einstellt, soll
# sofort sehen, dass es den Weg noch nicht gibt — nicht still lokal fahren.

from . import schleife

NOCH_NICHT = ("Der Weg über Sashas Server ist noch nicht verfügbar. "
              "Stell die Einstellung „ziel“ auf „direkt“ (eigener Schlüssel).")


def verfuegbar() -> bool:
    return False


def fahren(verlauf, *, anbieter, modell, system, tools, ausfuehren, **regler):
    yield schleife.fehler(NOCH_NICHT)
