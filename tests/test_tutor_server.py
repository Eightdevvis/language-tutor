"""Der Tutor-Server (tutor/server.py) mit dem Flask-Test-Client: Routen,
Zugangs-Tür, Ereignis vom Hub, Manifest."""
import os
import tomllib

import pytest

from tutor import config, dienst, memory, server, session, srs, staende, tools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def welt(tmp_path, monkeypatch):
    root = str(tmp_path)
    monkeypatch.setattr(tools, "_DATA_ROOT", root)
    monkeypatch.setattr(memory, "_DATA_DIR", root)
    monkeypatch.setattr(srs, "_DATA_ROOT", root)
    monkeypatch.setattr(config, "_overrides", {})
    sid = staende.anlegen(root, "T", lang="es", level=0)
    staende.waehlen(root, sid)
    session.deactivate()
    yield root
    session.deactivate()


@pytest.fixture
def client():
    return server.app.test_client()


def test_status_sagt_warum_nicht(welt, client):
    config.set_override("provider", "qwen")
    st = client.get("/api/tutor/status").get_json()
    assert st["available"] is False and "Schlüssel" in st["reason"]


def test_start_ohne_modell_503_mit_grund(welt, client):
    config.set_override("provider", "qwen")
    r = client.post("/api/tutor/start", json={})
    assert r.status_code == 503 and "Schlüssel" in r.get_json()["detail"]


def test_start_und_antwort_streamen(welt, client, monkeypatch):
    monkeypatch.setattr(session, "unavailable_reason", lambda: "")
    monkeypatch.setattr(memory, "remember", lambda *a, **k: None)
    from tutor import anbieter

    def fake(*a, **k):
        yield "¡Hola!"
    monkeypatch.setattr(anbieter, "fahren", fake)
    r = client.post("/api/tutor/start", json={})
    assert b"Hola" in r.data and b'"done": true' in r.data
    r = client.post("/api/tutor/respond", json={"text": "hola"})
    assert b"Hola" in r.data
    assert client.post("/api/tutor/respond", json={}).status_code == 400


def test_config_lehnt_sprache_ab_und_kennt_optik(welt, client):
    assert "error" in client.post("/api/tutor/config", json={"lang": "zh"}).get_json()
    cf = client.post("/api/tutor/config", json={"optik": "alt"}).get_json()
    assert cf["optik"] == "alt" and cf["lang"] == "es"


def test_staende_ueber_http(welt, client):
    r = client.post("/api/tutor/staende", json={"name": "Lena", "lang": "de"})
    assert r.status_code == 200 and r.get_json()["ok"]
    assert client.post("/api/tutor/staende/waehlen", json={}).status_code == 400
    assert client.get("/api/tutor/assessment").get_json()["lang"] == "de"


def test_ereignis_anwesenheit_vom_hub(welt, client, monkeypatch):
    gepingt = []
    monkeypatch.setattr(session, "presence_ping", lambda: gepingt.append(1) or True)
    r = client.post("/hub/ereignis", json={"name": "anwesenheit"})
    assert r.status_code == 200 and r.get_json()["reagiert"] and gepingt
    config.set_override("presence_react", "0")
    assert client.post("/hub/ereignis", json={"name": "anwesenheit"}).get_json()["reagiert"] is False
    assert client.post("/hub/ereignis", json={"name": "mail.neu"}).status_code == 400


def test_fremder_rechner_braucht_den_zugangsschluessel(welt, client, monkeypatch, tmp_path):
    fremd = {"REMOTE_ADDR": "192.0.2.7"}
    assert client.get("/hub/gesund", environ_base=fremd).status_code == 401, \
        "ohne Schlüssel-Datei: fremde Rechner draußen"
    datei = tmp_path / "zugang"
    datei.write_text("geheim\n")
    monkeypatch.setenv("TUTOR_ZUGANG_DATEI", str(datei))
    assert client.get("/hub/gesund", environ_base=fremd).status_code == 401
    ok = client.get("/hub/gesund", environ_base=fremd,
                    headers={"Authorization": "Bearer geheim"})
    assert ok.status_code == 200
    assert client.get("/hub/gesund").status_code == 200, "dieser Rechner immer"


def test_stimme_fehlt_gibt_503(welt, client, monkeypatch):
    monkeypatch.setattr(server.stimme, "sprechen", lambda *a, **k: b"")
    assert client.post("/api/speak", json={"text": "hola"}).status_code == 503
    assert client.post("/api/speak", json={}).status_code == 400


def test_manifest_nach_hub_bauplan():
    with open(os.path.join(ROOT, "app.toml"), "rb") as f:
        m = tomllib.load(f)
    assert m["name"] == "tutor" and m["start"] == "python -m tutor.server"
    assert set(m["rechte"]) == {"modell", "ereignis:anwesenheit", "mikro", "lautsprecher"}
    assert set(m["ansichten"]) == {"terminal", "fenster"}
    port = int(config.STANDARD["port"])
    assert m["adresse"].endswith(":%d" % port), "Adresse passt zum Standard-Port"
    routen = {r.rule for r in server.app.url_map.iter_rules()}
    assert m["ereignisse"]["ziel"] in routen


def test_dienst_status_ohne_absturz_wenn_session_kaputt(monkeypatch):
    def boom():
        raise RuntimeError("x")
    monkeypatch.setattr(session, "unavailable_reason", boom)
    st = dienst.status()
    assert st["available"] is False and st["reason"]
