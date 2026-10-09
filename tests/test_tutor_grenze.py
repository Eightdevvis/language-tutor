"""Die Hub-Regel (ZENTRALE hub_bauplan.md): eine App importiert keinen Code
außerhalb ihrer eigenen Wurzel. Und: die Modell-Leitung bekommt nie etwas
anderes als den Prompt, den Verlauf und die Werkzeuge des Tutors.

Auslöser: bis 08.10.2026 rief die Gedächtnis-Verdichtung des Tutors den
vollen Assistenten von ZENTRALE (mit Kalender-Werkzeugen) auf.
"""
import ast
import os
import sys

import pytest

from tutor import config, memory, session, srs, staende, tools
from tutor.modell import leitung

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Was ein Tutor-Modul importieren darf: Standardbibliothek, die Pakete aus
# requirements.txt, und sich selbst.
ERLAUBT_FREMD = {"flask", "anthropic", "openai", "fsrs", "pygame", "sounddevice",
                 "webrtcvad", "pytest", "numpy"}
EIGENE = {"tutor", "tests"}


def _module_des_repos():
    for ordner, _dirs, dateien in os.walk(ROOT):
        if any(t in ordner for t in ("venv", ".git", "__pycache__")):
            continue
        for d in dateien:
            if d.endswith(".py"):
                yield os.path.join(ordner, d)


def _top_imports(pfad):
    baum = ast.parse(open(pfad, encoding="utf-8").read(), pfad)
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            for a in knoten.names:
                yield a.name.split(".")[0]
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            yield knoten.module.split(".")[0]


def _geschwister(pfad):
    """Module neben der Datei (room.py importiert `sprites` als Skript)."""
    return {f[:-3] for f in os.listdir(os.path.dirname(pfad)) if f.endswith(".py")}


def test_kein_import_ausserhalb_der_eigenen_wurzel():
    std = set(sys.stdlib_module_names)
    fremd = []
    for pfad in _module_des_repos():
        nachbarn = _geschwister(pfad)
        for name in _top_imports(pfad):
            if name in std or name in ERLAUBT_FREMD or name in EIGENE or name in nachbarn:
                continue
            fremd.append(f"{os.path.relpath(pfad, ROOT)}: {name}")
    assert not fremd, "Import außerhalb der Wurzel (Hub-Regel): %s" % fremd


def test_keine_pfade_in_zentrales_code():
    """Auch nicht per Dateipfad laden (so lud das Zimmer bis 09.10. den
    Zugangs-Klienten aus ZENTRALE)."""
    treffer = []
    for pfad in _module_des_repos():
        if os.path.basename(pfad).startswith("test_"):
            continue
        src = open(pfad, encoding="utf-8").read()
        for verboten in ("spec_from_file_location", "'core'", '"core"',
                         "tui/ansichten", "zentrale_tui.py'"):
            if verboten in src:
                treffer.append(f"{os.path.relpath(pfad, ROOT)}: {verboten}")
    assert not treffer, treffer


@pytest.fixture
def welt(tmp_path, monkeypatch):
    root = str(tmp_path)
    monkeypatch.setattr(tools, "_DATA_ROOT", root)
    monkeypatch.setattr(memory, "_DATA_DIR", root)
    monkeypatch.setattr(srs, "_DATA_ROOT", root)
    monkeypatch.setattr(config, "_overrides", {})
    sid = staende.anlegen(root, "T", lang="es", level=0)
    staende.waehlen(root, sid)
    return root


def _fang(monkeypatch):
    gesehen = []

    def fake(anbieter, modell, verlauf, *, system, tools, ausfuehren, **kw):
        gesehen.append({"system": system, "verlauf": verlauf, "tools": tools,
                        "ausfuehren": ausfuehren})
        yield "{}"
    monkeypatch.setattr(leitung, "fahren", fake)
    return gesehen


def test_gespraech_bekommt_nur_tutor_prompt_und_tutor_werkzeuge(welt, monkeypatch):
    gesehen = _fang(monkeypatch)
    monkeypatch.setattr(memory, "remember", lambda *a, **k: None)
    session.deactivate(); session.activate()
    try:
        list(session.respond_stream("hola"))
    finally:
        session.deactivate()
    g = gesehen[0]
    namen = {t["function"]["name"] for t in g["tools"]}
    assert namen == {t["function"]["name"] for t in tools.tools_for("es")}
    assert g["ausfuehren"] is tools.execute_tool, "nur die Allowlist des Tutors führt aus"
    prof = session.langs.get("es")
    assert g["system"].startswith(prof["system_prompt"].split("{native}")[0])
    for fremd in ("read_calendar", "kalender", "Kalender", "Termin", "## Jetzt"):
        assert fremd not in g["system"], fremd


def test_verdichtung_ohne_werkzeuge_nur_eigene_notizen(welt, monkeypatch):
    gesehen = _fang(monkeypatch)
    monkeypatch.setattr(memory, "_verdichter", lambda p: "cloud")
    memory.remember("tengo hambre", "¿quieres comer?", "es", "qwen", "qwen-plus")
    g = gesehen[0]
    assert g["tools"] == [] and g["ausfuehren"] is None, "Verdichtung: keine Werkzeuge"
    assert g["system"] == memory._DISTILL_SYS
    assert len(g["verlauf"]) == 1 and "tengo hambre" in g["verlauf"][0]["content"]


def test_leitung_macht_aus_none_keine_werkzeuge(monkeypatch):
    """tools=None hieß in ZENTRALE „alle Kern-Werkzeuge". Hier heißt es: keine."""
    from tutor.modell import weg_ollama
    gesehen = {}

    def fake(verlauf, **kw):
        gesehen.update(kw)
        yield "x"
    monkeypatch.setattr(weg_ollama, "fahren", fake)
    list(leitung.fahren("local", None, [], system="S", tools=None, ausfuehren=None))
    assert gesehen["tools"] == []
