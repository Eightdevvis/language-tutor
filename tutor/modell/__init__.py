# tutor/modell/ — die eigene Modell-Leitung des Tutors (seit 2026-10-09).
#
# Bis hierher fuhr der Tutor auf der Straße von ZENTRALE (kern.fahren). Seit
# er ein eigenes Programm ist, hat er seine eigene, kleine Leitung — portiert
# aus ZENTRALE (core/providers.py, cloud.py, cloud_openai.py,
# werkzeug_schleife.py), aber nur das, was der Tutor braucht: kein Gedächtnis
# des Assistenten, kein Erlaubnis-Gate, keine Kern-Werkzeuge. Was hier
# reingeht, ist IMMER der Prompt des Tutors und seine Werkzeuge — sonst nichts
# (tests/test_tutor_leitung.py wacht darüber).
#
#   leitung.py         der eine Einstieg: fahren(...) — direkt oder über den Hub
#   anbieter_liste.py  welche Anbieter es gibt (Endpunkt, Art, Datenschutz)
#   schluessel.py      der eigene Schlüssel (Datei außerhalb des Repos)
#   kosten.py          Preise, Buchung, Monatsbudget des Tutors
#   schleife.py        Modell fragen → Werkzeuge → nächste Runde
#   weg_*.py           je Dialekt ein Adapter (Anthropic, OpenAI-kompatibel, Ollama)
#   hub.py             Ziel „hub": später Sashas Server, heute ein Platzhalter
