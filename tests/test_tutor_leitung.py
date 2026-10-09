"""Die eigene Modell-Leitung des Tutors (seit 2026-10-09).

Kein echter Modellaufruf: die Clients sind gefälscht. Geprüft wird, was
Sasha spürt — welcher Weg fährt, wann er NICHT fährt (kein Schlüssel,
unsichere Schlüssel-Datei, Budget alle, Ziel hub) und dass gebucht wird.
"""
import json
import os
import types

import pytest

from tutor import config, memory, session, srs, staende, tools
from tutor.modell import kosten, leitung, schluessel, weg_ollama, weg_openai, weg_anthropic


# ── gefälschter OpenAI-kompatibler Client ──────────────────────────────

def _chunk(content=None, tool=None, usage=None):
    tcs = None
    if tool:
        name, args = tool
        tcs = [types.SimpleNamespace(index=0, id="t1", function=types.SimpleNamespace(
            name=name, arguments=args))]
    delta = types.SimpleNamespace(content=content, tool_calls=tcs, reasoning_content=None)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta)], usage=usage)


def _usage(rein=100, raus=20):
    return types.SimpleNamespace(prompt_tokens=rein, completion_tokens=raus,
                                 prompt_tokens_details=None)


class FakeOpenAI:
    def __init__(self, runden):
        self.runden, self.calls = list(runden), []
        fake = self

        class _C:
            @staticmethod
            def create(**kw):
                fake.calls.append(json.loads(json.dumps(kw, default=str)))
                return iter(fake.runden.pop(0))
        self.chat = types.SimpleNamespace(completions=_C)


def _text(*teile):
    return [_chunk(content=t) for t in teile] + [
        types.SimpleNamespace(choices=[], usage=_usage())]


def _tool(name, args):
    return [_chunk(tool=(name, args)), types.SimpleNamespace(choices=[], usage=_usage())]


# ── Umgebung ───────────────────────────────────────────────────────────

@pytest.fixture
def schluessel_datei(tmp_path, monkeypatch):
    pfad = tmp_path / "schluessel"
    pfad.write_text("# Testschlüssel\nqwen = test-qwen\nclaude = test-claude\n")
    os.chmod(pfad, 0o600)
    monkeypatch.setenv("TUTOR_SCHLUESSEL_DATEI", str(pfad))
    return pfad


@pytest.fixture
def welt(tmp_path, monkeypatch):
    root = str(tmp_path / "daten")
    os.makedirs(root)
    monkeypatch.setenv("TUTOR_DATEN_ORDNER", root)
    monkeypatch.setattr(tools, "_DATA_ROOT", root)
    monkeypatch.setattr(memory, "_DATA_DIR", root)
    monkeypatch.setattr(srs, "_DATA_ROOT", root)
    monkeypatch.setattr(config, "_overrides", {})
    monkeypatch.setattr(memory, "remember", lambda *a, **k: None)
    sid = staende.anlegen(root, "T", lang="es", level=0)
    staende.waehlen(root, sid)
    return root


# ── Schlüssel ──────────────────────────────────────────────────────────

def test_ohne_schluessel_klare_meldung_statt_aufruf(welt):
    out = list(leitung.fahren("qwen", None, [], system="S", tools=[], ausfuehren=None))
    assert len(out) == 1 and "kein Schlüssel" in out[0]["fehler"]


def test_schluessel_fuer_andere_lesbar_wird_nicht_genommen(schluessel_datei, welt):
    os.chmod(schluessel_datei, 0o644)
    assert schluessel.hat("qwen") is False
    assert "lesbar" in leitung.warum_nicht("qwen")
    os.chmod(schluessel_datei, 0o600)
    assert schluessel.hat("qwen") and leitung.warum_nicht("qwen") == ""


def test_kein_rueckgriff_auf_fremde_umgebungs_schluessel(welt, monkeypatch):
    """Ein Schlüssel in der Umgebung (z. B. von ZENTRALE) zählt NICHT."""
    monkeypatch.setenv("DASHSCOPE_API_KEY", "fremd")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fremd")
    assert not schluessel.hat("qwen") and not schluessel.hat("claude")


# ── Ziel, Budget ───────────────────────────────────────────────────────

def test_ziel_hub_ist_noch_nicht_da(schluessel_datei, welt):
    config.set_override("ziel", "hub")
    out = list(leitung.fahren("qwen", None, [], system="S", tools=[], ausfuehren=None))
    assert "noch nicht verfügbar" in out[0]["fehler"]
    assert "noch nicht verfügbar" in leitung.warum_nicht("qwen")


def test_budget_aufgebraucht_faehrt_nicht(schluessel_datei, welt, monkeypatch):
    config.set_override("monatsbudget_euro", 0.01)
    kosten.buchen("qwen-max", rein=100_000, raus=100_000)
    assert kosten.budget_aufgebraucht()
    gerufen = []
    monkeypatch.setattr(weg_openai, "_client", lambda *a: gerufen.append(1))
    out = list(leitung.fahren("qwen", None, [], system="S", tools=[], ausfuehren=None))
    assert "Monatsbudget" in out[0]["fehler"] and not gerufen


def test_kosten_je_rechner_eigene_datei_summe_ueber_alle(welt):
    kosten.buchen("qwen-plus", rein=1_000_000)
    andere = os.path.join(welt, "kosten", "anderer-rechner.json")
    with open(andere, "w") as f:
        json.dump({kosten._monat(): {"euro": 1.0, "aufrufe": 1}}, f)
    assert kosten.monat_euro() == pytest.approx(1.0 + 0.40 * kosten.USD_EUR)


# ── Wege mit gefälschtem Client ────────────────────────────────────────

def test_tutor_zug_ueber_openai_weg(schluessel_datei, welt, monkeypatch):
    c = FakeOpenAI([_tool("express", '{"action": "wave"}'), _text("¡Ho", "la!")])
    monkeypatch.setattr(weg_openai, "_client", lambda base, key: c)
    config.set_override("provider", "qwen")
    config.set_override("model", "qwen-plus")
    session.deactivate(); session.activate()
    try:
        out = list(session.respond_stream("hola"))
    finally:
        session.deactivate()
    assert "".join(out) == "¡Hola!", "nur Text ans Zimmer, keine Events"
    erste = c.calls[0]
    assert erste["max_tokens"] == 140 and erste["temperature"] == 0.4
    assert erste["model"] == "qwen-plus"
    assert erste["messages"][0]["role"] == "system"
    assert kosten.monat_euro() > 0, "Cloud-Aufrufe werden gebucht"
    assert c.calls[1]["messages"][-1]["role"] == "tool", "Werkzeug-Ergebnis geht zurück"


class _FakeAnthropicStrom:
    def __init__(self, final):
        self.final = final

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        d = types.SimpleNamespace(type="text_delta", text="Hallo")
        return iter([types.SimpleNamespace(type="content_block_delta", delta=d)])

    def get_final_message(self):
        return self.final


def test_anthropic_weg_mit_effort_und_buchung(schluessel_datei, welt):
    final = types.SimpleNamespace(
        stop_reason="end_turn", content=[],
        usage=types.SimpleNamespace(input_tokens=10, output_tokens=5,
                                    cache_read_input_tokens=0,
                                    cache_creation_input_tokens=0))
    gesehen = {}

    def stream(**kw):
        gesehen.update(kw)
        return _FakeAnthropicStrom(final)
    client = types.SimpleNamespace(messages=types.SimpleNamespace(stream=stream))
    out = list(weg_anthropic.fahren([{"role": "user", "content": "hi"}],
                                    modell="claude-sonnet-5", system="S", tools=[],
                                    ausfuehren=None, schluessel="x", max_tokens=2000,
                                    effort="low", client=client))
    assert out == ["Hallo"]
    assert gesehen["output_config"] == {"effort": "low"}
    assert "tools" not in gesehen, "ohne Werkzeuge kein leeres Feld"
    assert gesehen["system"][0]["text"] == "S"
    assert kosten.monat_euro() > 0


def test_ollama_weg_werkzeug_runde(welt):
    antworten = [
        {"message": {"role": "assistant", "content": "",
                     "tool_calls": [{"function": {"name": "express",
                                                  "arguments": {"action": "nod"}}}]}},
        {"message": {"role": "assistant", "content": "listo"}},
    ]
    gesendet = []

    def senden(pfad, koerper):
        gesendet.append(json.loads(json.dumps(koerper)))
        return antworten.pop(0)
    ausgefuehrt = []
    out = list(weg_ollama.fahren([{"role": "user", "content": "hola"}], modell="m",
                                 system="S", tools=[{"x": 1}],
                                 ausfuehren=lambda n, a: ausgefuehrt.append((n, a)) or "ok",
                                 senden=senden))
    assert out[-1] == "listo"
    assert ausgefuehrt == [("express", {"action": "nod"})]
    assert gesendet[1]["messages"][-1] == {"role": "tool", "content": "ok"}


def test_fehler_eines_werkzeugs_bricht_den_zug_nicht_ab(welt):
    antworten = [
        {"message": {"content": "", "tool_calls": [{"function": {"name": "kaputt",
                                                               "arguments": {}}}]}},
        {"message": {"content": "trotzdem"}},
    ]

    def boom(n, a):
        raise RuntimeError("geht nicht")
    out = list(weg_ollama.fahren([], modell="m", system="S", tools=[], ausfuehren=boom,
                                 senden=lambda p, k: antworten.pop(0)))
    assert out[-1] == "trotzdem"


def test_unbekannter_anbieter_fehler_statt_absturz():
    out = list(leitung.fahren("gibtsnicht", None, [], system="S", tools=[], ausfuehren=None))
    assert "gibtsnicht" in out[0]["fehler"]


# ── Verdichtung des Gedächtnisses ──────────────────────────────────────

def test_verdichter_lokal_vor_cloud(monkeypatch):
    monkeypatch.setattr(weg_ollama, "erreichbar", lambda *a, **k: True)
    assert memory._verdichter("qwen") == "local"
    monkeypatch.setattr(weg_ollama, "erreichbar", lambda *a, **k: False)
    monkeypatch.setattr(leitung, "warum_nicht", lambda n: "")
    assert memory._verdichter("qwen") == "cloud"
    monkeypatch.setattr(leitung, "warum_nicht", lambda n: "kein Schlüssel")
    assert memory._verdichter("qwen") is None, "nichts da → nicht merken"
