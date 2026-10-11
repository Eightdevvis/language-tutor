# Sprach-Tutor — Index

Der Tutor ist ein **eigenes Programm** (dieses Repo, seit 2026-10-09; vorher
in ZENTRALE unter `tutor/`). Er ist die erste App nach ZENTRALEs Hub-Bauplan:
eigener Server-Prozess, eigener Schlüssel, eigenes Budget, eigene
Einstellungen. Was er vom Hub will, steht in `app.toml`. Einstieg zum
Betrieb: [../README.md](../README.md).

Die Doku unten stammt zum Teil aus der Zeit in ZENTRALE; wo dort `core/…`,
`ui/routen/…` oder `/api/tutor` über ZENTRALE steht, ist das Geschichte —
die Struktur von heute steht im Bauplan.

| Was du wissen willst | Datei |
|---|---|
| **Einstieg.** Aufbau des Persona-Portals, Sprachprofile, Vokabel-Modell, austauschbare Provider | [tutor_system.md](tutor_system.md) |
| **Bauplan** — der Blueprint: Struktur (Skelett/Inhalt/Naht/Front), Verzeichnisbaum mit Rollen, Routen, Checkliste neue Sprache; `tests/test_tutor_bauplan.py` erzwingt Synchronität | [bauplan.md](bauplan.md) |
| **Naturalisierung** — die Referenz für den Ausbau: Kern (leicht anfangen, organisch mitlernen), Umgebungs-Kontext, Skill `no_entiendo`, Tools heute/geplant | [naturalisierung.md](naturalisierung.md) |
| Wie die Persona zuverlässig kurz und in der Zielsprache bleibt — Testläufe gegen echtes qwen-plus | [tutor_persona_tuning.md](tutor_persona_tuning.md) |
| Die Roleplay-Features (Zimmer, Shop, Kisten) und warum sie so entschieden wurden | [tutor_roleplay_features.md](tutor_roleplay_features.md) |
| Wie die Persona aussieht: gemalte Puppe statt Polygone, Drehpunkte, Mal-Schablone | [tutor_puppe.md](tutor_puppe.md) |
| **Diagnose 2026-10-08** — Sashas Beschwerden (Dauergerede, Zufall, Niveau, „que?", Mikro, STT, Optik, Bilder) je mit Ursache (Datei:Zeile), Strategie, was gebaut ist, was offen bleibt | [diagnose_2026-10-08.md](diagnose_2026-10-08.md) |

## Grenze zum Hub

Der Tutor hat sein **eigenes** Gedächtnis (`tutor/memory.py`, Notiz-Modell) —
**nicht** das Gedächtnis von Sashas Assistenten in ZENTRALE. Die beiden
Speicher fassen sich nie an, und seit dem Umzug kann der Tutor auch keinen
Code von ZENTRALE mehr aufrufen (`tests/test_tutor_grenze.py`).

Die harte Cloud→Lokal-Trennung (was die Tutor-KI sieht, Choke-Point
`_ALLOWED`, wer sie aufweicht): [tutor_system.md](tutor_system.md) →
„Cloud→Lokal-Trennung".
