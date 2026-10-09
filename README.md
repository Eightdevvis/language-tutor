# Sprach-Tutor (language-tutor)

Lucía & Co.: eine Persona, die im Zimmer wohnt und mit dir in der Zielsprache
redet. Seit 2026-10-09 ein eigenes Programm — vorher Teil von ZENTRALE.
Es ist die erste **App** nach ZENTRALEs Hub-Bauplan: ZENTRALE startet sie und
schickt ihr Ereignisse („jemand ist im Raum"), sonst kennen sich die beiden
nicht. Was die App vom Hub will, steht in `app.toml`.

## Teile

- **Server** (`tutor/server.py`) — der eigene Prozess, lauscht standardmäßig
  auf diesem Rechner, Port 5070. Hier denkt der Tutor.
- **Zimmer** (`tutor/room.py`) — das Fenster mit der Figur. Rechnet nichts,
  redet nur mit dem Server.
- **Stimme** — Hören (Whisper) und Sprechen (TTS) sind eigene Dienste
  (heute noch aus ZENTRALE, Ports 5050/5051). Der Tutor kennt nur ihre Adresse.

Doku: `docs/INDEX.md`, Struktur: `docs/bauplan.md`.

## Einrichten (was Sasha tun muss)

1. **Python-Umgebung.** Am einfachsten eine eigene virtuelle Umgebung im
   Repo-Ordner (Ordnername `venv`) mit den Paketen aus `requirements.txt`.
   Bis dahin geht auch die Umgebung von ZENTRALE — die hat alles Nötige.
2. **Schlüssel.** Lege die Datei `~/.config/language-tutor/schluessel` an.
   Je Anbieter eine Zeile `name = schlüssel`, z. B. eine Zeile für `qwen`
   und eine für `claude`. Danach die Rechte der Datei so einstellen, dass
   nur du sie lesen und schreiben darfst — sonst nimmt der Tutor sie nicht.
   Ohne Schlüssel geht nur das lokale Modell (Ollama).
3. **Budget.** Standard sind 5 € im Monat für die Cloud. Ändern in
   `~/.config/language-tutor/einstellungen.json` (Schlüssel
   `monatsbudget_euro`). Ist es aufgebraucht, sagt das Zimmer es klar.
4. **Lernstände.** Der Tutor findet Sashas bisherige Lernstände von selbst
   im alten Ordner von ZENTRALE (`ZENTRALE/tutor/data`, wenn dieses Repo
   daneben liegt) und sagt beim Start, dass er dort liest. Zum Umziehen den
   ganzen Ordner nach `language-tutor/tutor/data` verschieben — vorher
   Server und Zimmer schließen. Oder den Ort mit `daten_ordner` in
   `einstellungen.json` festlegen.

## Einstellungen

Alle mit Standardwert in `tutor/config.py` (`STANDARD`). Ändern in
`~/.config/language-tutor/einstellungen.json`, oder für einen Versuch als
Umgebungsvariable `TUTOR_<NAME>`. Wichtig:

| Einstellung | Wozu |
|---|---|
| `ziel` | `direkt` (eigener Schlüssel) oder `hub` (später Sashas Server — noch nicht da) |
| `provider`, `model` | welcher Anbieter, welches Modell (sonst das Sprachprofil) |
| `monatsbudget_euro` | Kosten-Deckel je Monat |
| `host`, `port` | wo der Server lauscht |
| `whisper_url`, `tts_url` | wo Hören und Sprechen laufen |
| `tutor_optik` | `pixel` oder `alt` |
| `presence_react` | `0` = nicht reagieren, wenn jemand den Raum betritt |

## Zimmer an der Wand (Pi), Server am PC

Dann muss der Server im Heimnetz lauschen (`host` auf die Netz-Adresse oder
„alle"), und beide Rechner brauchen dieselbe Zeile in
`~/.config/language-tutor/zugang` — ohne die weist der Server fremde Rechner
ab. Auf dem Pi reicht vom Repo das Zimmer (`tutor/room.py`, `mikro.py`,
`sprites.py`, `pixel_zimmer.py`, `zugang.py`, `assets/`).

## Tests

Alle Tests liegen in `tests/` und fassen keine echten Daten, Einstellungen
oder Schlüssel an (`tests/conftest.py`). Laufen mit pytest aus der
Python-Umgebung (eigene oder die von ZENTRALE).
