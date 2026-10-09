# Bauplan eines Tutors — der Blueprint

**Wozu:** Sasha, 2026-09-17: ein einheitliches Dokument, das den Bauplan eines
Tutors festhält, damit künftige Tutoren (neue Sprachen, neue Personas, ein
zweiter Knoten) nach demselben Muster entstehen. Es hält **Struktur und
Artefakte**, nicht Verhalten — das steht in `tutor_system.md` (Mechanik,
Historie) und `naturalisierung.md` (Ausbau).

**Es driftet nicht, weil ein Test es erzwingt:** `tests/test_tutor_bauplan.py`
liest die Artefakt-Tabellen dieser Datei und prüft, dass jeder Pfad existiert,
jedes aktive Sprachpaket vollständig ist und jede Route hier auch in
`tutor/server.py` steht (und umgekehrt). **Pflegeregel:** Struktur ändern → Bauplan im
selben Commit ändern, sonst wird der Test rot.

## 1. Die Struktur darüber

Seit 2026-10-09 ist der Tutor ein **eigenes Programm** (Repo `language-tutor`)
und die erste App nach ZENTRALEs Hub-Bauplan. ZENTRALE (der Hub) startet ihn
und schickt ihm Ereignisse; sonst kennen sich die beiden nicht.

```
                    ┌────────────────────────────────────────────────────┐
                    │  INHALT  — pro Sprache/Land, tutor/langs/<code>/    │
                    │  Persona, Prompt, Kernwörter, Texte, Seeds, Avatar  │
                    └───────────────────────┬────────────────────────────┘
                                            │ Profil (langs.get)
 ┌──────────────────────────────────────────▼──────────────────────────────┐
 │  SKELETT — für jede Sprache gleich, tutor/*.py                          │
 │  session (Turn, Prompt-Bau)  tools (Vokabel, Spiel, Tool-Calls)         │
 │  skills  ansprache  memory  srs  staende  config  debug                 │
 │  anbieter ──► modell/ (eigene Leitung: Schlüssel, Budget, Wege)         │
 └───────────────┬──────────────────────────────────────────┬─────────────┘
                 │                                            │ HTTP (/api/tutor/*, /api/speak, /api/transcribe)
        tutor/dienst.py ──► tutor/server.py (eigener Prozess, :5070)
                 ▲                                    ┌───────▼────────────────────────┐
   HTTP /hub/ereignis (anwesenheit)                   │  FRONT — tutor/room.py (Zimmer) │
                 │                                    │  hört, spricht, zeigt; rechnet  │
        ZENTRALE (Hub): startet App + Zimmer,         │  nichts; nur stdlib + pygame    │
        schickt abonnierte Ereignisse (app.toml)      └────────────────────────────────┘
        Stimm-Dienste (Whisper :5050, TTS :5051) laufen als eigene Prozesse;
        der Tutor kennt nur ihre Adresse (whisper_url, tts_url).
```

Vier Regeln, die alles zusammenhalten:
1. **Ein Spielstand = eine Sprache + ein Level.** Die aktive Sprache kommt nur
   aus dem aktiven Stand (`staende.aktive_sprache`). Es gibt keine zweite Quelle.
2. **Skelett kennt keine Sprache.** Alles Sprachliche kommt aus dem Profil des
   Pakets; der Code fragt `langs.get(code)`.
3. **Das Zimmer ist dumm.** `room.py` rechnet nichts und braucht nur stdlib +
   pygame (+ `mikro`, `sprites`, `pixel_zimmer`, `zugang`), damit es auf dem Pi
   ohne Server-Code läuft.
4. **Kein Import außerhalb dieses Repos** (Hub-Regel). `tests/test_tutor_grenze.py`
   prüft das, und dass die Modell-Leitung nur den Tutor-Prompt bekommt.

## 2. Verzeichnisbaum mit Rolle je Artefakt

Diese Tabelle liest der Drift-Test: jeder Pfad muss existieren.

| Pfad | Rolle |
|---|---|
| `app.toml` | Manifest für den Hub: name, version, start, adresse, ansichten, rechte, abonnierte Ereignisse |
| `requirements.txt` | Was Server und Zimmer brauchen |
| `tutor/__init__.py` | Paket |
| `tutor/server.py` | Der eigene Prozess (`python -m tutor.server`): Flask-Routen (Abschnitt 3), Zugangs-Tür |
| `tutor/dienst.py` | Was der Server anbietet, ohne HTTP: Status, Einstellungen, Drill, Spielstände, Ereignisse vom Hub (vorher ZENTRALE `core/tutor_port.py`) |
| `tutor/stimme.py` | Reicht Hören/Sprechen an Whisper/TTS weiter (Einstellungen `whisper_url`, `tts_url`) |
| `tutor/zugang.py` | Zugangsschlüssel: Server weist fremde Rechner ohne Schlüssel ab, Zimmer schickt ihn mit |
| `tutor/pfade.py` | Wo Daten, Einstellungen, Schlüssel liegen (inkl. Umzugshilfe: alter ZENTRALE-Ordner) |
| `tutor/session.py` | Ein Turn: Eingabe auswerten (spoken/listened, „que?"), Ruhe-Regel + Anlass (über `ansprache`), System-Prompt-Bau (Persona + Vokabel-Status + Niveau + Kern-Hinweis + Gedächtnis + `{native}`), Streaming, Nachkontrolle, Token-Guard gegen Stand-Wechsel |
| `tutor/tools.py` | Vokabel-Modell (spoken/listened → Status), Kernwörter, Spiel (Münzen/Kisten/Teile), Level, Glosse (Muttersprache), die Tool-Calls fürs Modell |
| `tutor/skills.py` | Situations-Auslöser (deterministisch), erster: `no_entiendo` |
| `tutor/ansprache.py` | WANN sie von sich aus spricht, WOZU, WIE SCHWER, Schlüsselwort für „que?" |
| `tutor/memory.py` | Persona-Gedächtnis (Notizen je Stand), Verdichtung nach dem Turn mit Token-Prüfung |
| `tutor/srs.py` | Langzeit-Wiederholung (FSRS) je Stand |
| `tutor/staende.py` | Spielstände: `stand.json {name, lang, level}`, `stand_lock`, `pfad()` weigert fremde Sprache, `token()/pruefen()`, Migration |
| `tutor/config.py` | Eigene Einstellungen (Liste `STANDARD`): Modell, Budget, Ziel, Optik, Stimme, Server — **kein** lang, **kein** Schlüssel |
| `tutor/anbieter.py` | Naht zur Modell-Leitung: Anbieter-Liste fürs UI, Regler max_tokens/temperature/effort, `fahren()` |
| `tutor/modell/__init__.py` | Die eigene Modell-Leitung (seit 2026-10-09, portiert aus ZENTRALE) |
| `tutor/modell/leitung.py` | Der eine Einstieg `fahren()`; Ziel `direkt` (eigener Schlüssel) oder `hub` (Platzhalter); `warum_nicht()` |
| `tutor/modell/anbieter_liste.py` | Anbieter: Art, Endpunkt, Standard-Modell, Datenschutz |
| `tutor/modell/schluessel.py` | Eigener Schlüssel aus `~/.config/language-tutor/schluessel` (nur mit Rechten 600) |
| `tutor/modell/kosten.py` | Preise, Buchung je Rechner, Monatsbudget |
| `tutor/modell/schleife.py` | Modell fragen → Werkzeuge → nächste Runde (ohne Gate, ohne Kern-Werkzeuge) |
| `tutor/modell/weg_anthropic.py` | Anthropic-Dialekt |
| `tutor/modell/weg_openai.py` | OpenAI-kompatibler Dialekt (qwen & Co.) |
| `tutor/modell/weg_ollama.py` | Lokales Ollama |
| `tutor/modell/hub.py` | Ziel `hub`: später Sashas Server (Schlüssel nie beim Kunden), heute klare Meldung |
| `tutor/debug.py` | Devtool-Ereignisbus (`emit`, SSE über `/api/tutor/debug/stream`) |
| `tutor/room.py` | Das Zimmer: pygame-Fenster, Stimme, Persona-Figur, Esc-Menü, Hauptmenü (Stände), Drill als Spiel |
| `tutor/mikro.py` | Das Ohr des Zimmers: Dauer-Mikro → VAD → fertige Äußerung (WAV) + Geräusch-Signal |
| `tutor/sprites.py` | Lädt die Figur (Rig + gemalte Teile) |
| `tutor/pixel_zimmer.py` | Das Zimmer in Pixel-Optik; Einstellung `tutor_optik` = `pixel` (Standard) / `alt` |
| `tutor/gelenke.py` | Drehpunkte/Posen der Figur |
| `tutor/schablone.py` | Mal-Schablone für neue Figuren |
| `tutor/langs/__init__.py` | Paket-Discovery: jeder Ordner mit `PROFILE` ist eine Sprache |
| `tutor/langs/base.py` | `profile()`, DEFAULTS, `load_text/load_json` |
| `tutor/langs/PROMPT_TEMPLATE.en.md` | Sprach-neutraler Master-Prompt (Roleplay-Rahmen), Vorlage jeder Übersetzung |
| `tutor/prompts/` | Kern-nahe Prompt-Bausteine (Tools, Nudge, Fallback) |
| `tutor/assets/figuren/` | Eine Figur je Ordner (`rig.json`, Teile-PNGs) |
| `tutor/assets/figuren/lucia/rig.json` | Bauplan der Figur Lucía |
| `tutor/assets/PermanentMarker-Regular.ttf` | Handschrift für die Karteikarte |
| `tutor/data/tutor_config.json.example` | Alte Vorlage der Einstellungen (wird noch gelesen; neu: `~/.config/language-tutor/einstellungen.json`) |
| `werkzeuge/tutor_devtools.py` | Terminal-Devtool: Prompt, Antworten, Tool-Calls, Vokabel, Skills live (gegen `/api/tutor/debug/stream`) |
| `tests/conftest.py` | Biegt Daten, Einstellungen, Schlüssel auf Wegwerf-Ordner |
| `tests/test_tutor_staende.py` | Spielstände, Bluten, Level, Glosse |
| `tests/test_tutor_skills.py` | Skill-Auslöser |
| `tests/test_tutor_wortregel.py` | Nur Wörter der Zielsprache in die Vokabelliste |
| `tests/test_tutor_isolation.py` | Stände bluten nicht: Vokabeln, Gedächtnis, SRS, Spiel, Session-Guard, Löschen |
| `tests/test_tutor_room_flows.py` | Zimmer headless gegen Fake-Backend |
| `tests/test_tutor_pixel.py` | Pixel-Optik headless, Einstellung tutor_optik |
| `tests/test_tutor_mikro.py` | Das Ohr ohne Hardware |
| `tests/test_tutor_ansprache.py` | Ruhe, Anlass, Niveau, „que?" |
| `tests/test_tutor_leitung.py` | Modell-Leitung: Ziele, Schlüssel (Rechte), Budget, Wege mit gefälschtem Client, Verdichtung |
| `tests/test_tutor_grenze.py` | Hub-Regel: kein Import außerhalb des Repos; die Leitung bekommt nur den Tutor-Prompt |
| `tests/test_tutor_server.py` | Routen, Zugangs-Tür, Ereignis `anwesenheit`, Manifest |
| `tests/test_tutor_bauplan.py` | Dieser Bauplan gegen den Code |
| `docs/tutor_system.md` | Mechanik + Historie (Verhalten) |
| `docs/naturalisierung.md` | Ausbau-Referenz (Umgebung, Skills, geplante Tools) |

Laufzeit-Daten (gitignored, nicht im Test), im Datenordner (`tutor/pfade.py`):
`aktiver_stand`, `staende/<id>/stand.json`, `staende/<id>/<lang>/{vocab, game,
progress, structures, fsrs, persona_mem, persona_hist, news, tv}.json`,
`tutor_config.json` (alt), `kosten/<rechner>.json`, `vocab_images/`,
`persona_music/`. Außerhalb: `~/.config/language-tutor/{einstellungen.json,
schluessel, zugang}`.

## 3. Routen (`tutor/server.py`)

Der Drift-Test vergleicht diese Liste mit den `@app.route(…)` im Code — in
beide Richtungen.

| Route | Methode | Wozu |
|---|---|---|
| `/api/tutor/status` | GET | verfügbar? (mit Grund) aktiv? Stimme da? |
| `/api/tutor/config` | GET, POST | Einstellungen (provider, model, native, optik); `lang` wird abgelehnt |
| `/api/tutor/start` | POST | Session aktivieren + Begrüßung (`still: true` = nur aktivieren) |
| `/api/tutor/respond` | POST | ein User-Turn, streamt |
| `/api/tutor/nudge` | POST | Lage-Meldung (Stille / Ankunft), streamt |
| `/api/tutor/stop` | POST | Session beenden |
| `/api/tutor/room_state` | GET | Ausdruck, Laune, Gedanke, Musik, TV, Modus, Tempo, presence_age |
| `/api/tutor/assessment` | GET | Kernwörter + Lernstand fürs Drill |
| `/api/tutor/assessment/answer` | POST | Drill-Antwort verbuchen (Spiel-Ökonomie) |
| `/api/tutor/staende` | GET, POST | Stände listen / neu (`name, lang, level`) |
| `/api/tutor/staende/waehlen` | POST | Stand laden |
| `/api/tutor/staende/loeschen` | POST | Stand löschen |
| `/api/tutor/debug/stream` | GET | SSE für das Devtool |
| `/api/speak` | POST | Text → WAV (weiter an TTS) |
| `/api/transcribe` | POST | WAV → Text (weiter an Whisper) |
| `/api/sensor/<name>` | POST | Zimmer meldet „jemand ist da" (`motion`) |
| `/hub/gesund` | GET | Lebt der Server? (für den Hub) |
| `/hub/ereignis` | POST | Ereignis vom Hub, `{name, daten}`; heute `anwesenheit` |

## 4. Checkliste: eine neue Sprache

Der Drift-Test prüft für jedes Paket mit `enabled = True` die Pflichtdateien
und -felder. Ein Paket ist ein Ordner `tutor/langs/<code>/` — mehr Registrierung
gibt es nicht.

**Pflichtdateien**

| Datei | Inhalt |
|---|---|
| `__init__.py` | `PROFILE = profile(code, …)` mit den Pflichtfeldern unten |
| `prompt.md` | System-Prompt **in der Zielsprache**, Übersetzung von `PROMPT_TEMPLATE.en.md`; `{native}` bleibt Platzhalter |
| `vocab_hint.md` | ein Satz mit `{words}` (Zielsprache) |
| `expect.json` | Register-Leiter `[[grenze, text], …]` (Zielsprache); Grenze = Zahl der Wörter, die Sasha wirklich kennt (seit 2026-10-08 befüllt für es/de/zh) |
| `absichten.json` | Optional (fehlt → nur Ruhe-Regeln): Anlass-Texte in der Zielsprache `ankunft, nachhaken, stille, stille_ohne_ziel, nachfrage, zu_schwer` (Platzhalter `{letzte} {wort} {bedeutung} {woerter}`) |
| `core_vocab.json` | ≈76 Einträge `{word, reading, priority, category, gloss:{en, de}}`, Kategorien aus `room._CAT_DE` |
| `tool_texts.json` | Beschreibung der lebenden Tools in der Zielsprache (`introduce_new, express, get_structures, introduce_structure, increment_structure, watch_tv, turn_off_tv, play_music, stop_music, get_local_news, get_due_reviews, show_thought`) |
| `seeds/news.json`, `seeds/tv.json` | 8 leichte Themen, 8 Sendungen `{title, mood, level, note}` |

**Pflichtfelder im Profil:** `name, persona_name, country, enabled, reading,
stt_lang, tts_lang, provider, model, system_prompt, vocab_hint, core_vocab,
core_hint, situation` (10 Keys: `prefix suffix join open open_focus nudge_idle
nudge_focus_yes nudge_focus_no nudge_sound`), `status_labels` (5),
`vocab_labels` (`structs join sep`), `phrases` (die 28 Keys aus
`tools._DEFAULT_PHRASES`), `native_names`, `seeds`.

**Außerhalb des Pakets:** eine TTS-Engine für den Code in
ZENTRALEs `services/tts_service.py` (`_engines[<code>]`; der Stimm-Dienst lebt
noch dort), Whisper kennt die Sprache
(Code = ISO), eine Figur (`avatar` im Profil, Default `lucia`), Zeile in
`docs/tutor_system.md`. Sonst nichts.

**Was NICHT mehr dazugehört (Legacy):** `assessment_prompt.md`, Tool-Texte für
`mark_known`, `get_confirmed_vocab`, `get_testing_vocab`, `increment_correct_use`.

## 5. Datenflüsse

```
Mikro (Pi) ─VAD─► Segment ─► /api/transcribe ─► Text ─► skills.pruefen (loggt)
   ─► session.respond_stream: note_spoken → Prompt (Profil + Status + Kern + Gedächtnis)
   ─► Modell (provider) ─► Text + Tool-Calls (express / show_thought / …)
   ─► Zimmer: Blase, Geste, Gedanke; /api/speak ─► WAV ─► Lautsprecher (Mikro gegated)
   ─► danach: memory.remember (Thread, Token-geprüft), srs, Graduierung

Spielstand ──► aktive Sprache ──► Profil (Prompt, Persona, Stimme) und Pfade
   staende/<id>/<lang>/…   ◄── tools / memory / srs (nur diese Sprache, stand_lock)
```

## 6. Pflege

- Neuer Code-Baustein, neue Route, neues Paket → hier eintragen, im selben Commit.
- `tutor_system.md` beschreibt **Verhalten**, dieser Bauplan **Struktur**; wer
  beides in einer Datei sucht, sucht falsch.
- Verhalten, das noch nicht gebaut ist, steht in `naturalisierung.md`, nie hier.
