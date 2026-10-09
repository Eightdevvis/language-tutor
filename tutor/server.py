# tutor/server.py
#
# Der Tutor-Server — der eigene Prozess des Sprach-Tutors (seit 2026-10-09).
#
#   python -m tutor.server          (Adresse: Einstellungen host/port, Standard
#                                    127.0.0.1:5070)
#
# Bis hierher machte ZENTRALE das unter /api/tutor/* (ui/routen/tutor.py,
# core/tutor_port.py). Jetzt ist der Tutor die erste App nach ZENTRALEs
# Hub-Bauplan: eigenes Repo, eigener Prozess, eigener Schlüssel, eigenes
# Budget. ZENTRALE startet ihn höchstens und schickt ihm Ereignisse, die er in
# app.toml abonniert hat (POST /hub/ereignis). Er importiert nichts aus
# ZENTRALE (tests/test_tutor_grenze.py).
#
# Die Pfade sind dieselben wie vorher, damit das Zimmer (tutor/room.py) nur
# eine andere Adresse braucht. Routen-Liste: docs/bauplan.md, Abschnitt 3.

import json
import os
import sys

from flask import Flask, Response, jsonify, request, stream_with_context

if __package__ in (None, ""):          # als Skript gestartet
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tutor import config, debug, dienst, pfade, session, stimme, zugang  # noqa: E402

app = Flask(__name__)


def _nicht_verfuegbar():
    grund = session.unavailable_reason() or "Tutor nicht verfügbar"
    return jsonify({"error": "Tutor nicht verfügbar", "detail": grund}), 503


@app.before_request
def _tuer():
    """Fremde Rechner nur mit Zugangsschlüssel (tutor/zugang.py)."""
    if not zugang.erlaubt(request.remote_addr, request.headers.get("Authorization")):
        return jsonify({"error": "kein Zugang"}), 401
    return None


def _sse(tokens):
    def erzeugen():
        for t in tokens:
            yield f"data: {json.dumps({'token': t})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    return Response(stream_with_context(erzeugen()), content_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Sitzung ────────────────────────────────────────────────────────────

@app.route("/api/tutor/status")
def api_status():
    st = dienst.status()
    st.update(whisper=stimme.gesund("whisper_url"), tts=stimme.gesund("tts_url"))
    return jsonify(st)


@app.route("/api/tutor/config", methods=["GET", "POST"])
def api_config():
    body = (request.get_json(silent=True) or {}) if request.method == "POST" else {}
    return jsonify(dienst.einstellungen(changes=body, persist=bool(body.get("persist"))))


@app.route("/api/tutor/start", methods=["POST"])
def api_start():
    if not session.available():
        return _nicht_verfuegbar()
    if not session.is_active() or not session.passt_zum_stand():
        session.activate()
    body = request.get_json(silent=True) or {}
    if body.get("still"):
        # Wand-Modus: nur aktivieren, gesprochen wird erst, wenn jemand da ist.
        return jsonify({"ok": True, "active": session.is_active()})
    return _sse(session.respond_stream(user_text=None, focus=body.get("focus")))


@app.route("/api/tutor/respond", methods=["POST"])
def api_respond():
    if not session.available():
        return _nicht_verfuegbar()
    if not session.is_active():
        return jsonify({"error": "Keine aktive Tutor-Session"}), 400
    text = ((request.get_json(silent=True) or {}).get("text") or "").strip()
    if not text:
        return jsonify({"error": "kein Text"}), 400
    return _sse(session.respond_stream(user_text=text))


@app.route("/api/tutor/nudge", methods=["POST"])
def api_nudge():
    if not session.available():
        return _nicht_verfuegbar()
    if not session.is_active():
        return jsonify({"error": "Keine aktive Tutor-Session"}), 400
    body = request.get_json(silent=True) or {}
    return _sse(session.respond_stream(nudge=True, focus=body.get("focus"),
                                       sound=body.get("sound"),
                                       arrival=bool(body.get("arrival"))))


@app.route("/api/tutor/stop", methods=["POST"])
def api_stop():
    session.deactivate()
    return jsonify({"ok": True})


@app.route("/api/tutor/room_state")
def api_room_state():
    try:
        return jsonify(session.room_state())
    except Exception:
        return jsonify({})


# ── Drill + Spielstände (ohne Modell, darum ohne Verfügbarkeits-Prüfung) ──

@app.route("/api/tutor/assessment")
def api_assessment():
    return jsonify(dienst.assessment())


@app.route("/api/tutor/assessment/answer", methods=["POST"])
def api_assessment_answer():
    body = request.get_json(silent=True) or {}
    word = (body.get("word") or "").strip()
    result = (body.get("result") or "").strip()
    if not word or result not in ("known", "learned", "again"):
        return jsonify({"error": "word + result (known|learned|again) noetig"}), 400
    return jsonify(dienst.assessment_answer(word, result))


@app.route("/api/tutor/staende")
def api_staende():
    return jsonify(dienst.staende_liste())


@app.route("/api/tutor/staende", methods=["POST"])
def api_stand_anlegen():
    body = request.get_json(silent=True) or {}
    d = dienst.stand_anlegen((body.get("name") or "").strip() or None,
                             lang=(body.get("lang") or "").strip().lower() or None,
                             level=int(body.get("level") or 0))
    return jsonify(d), (200 if d.get("ok") else 400)


def _mit_id(fn):
    sid = ((request.get_json(silent=True) or {}).get("id") or "").strip()
    if not sid:
        return jsonify({"ok": False, "error": "id noetig"}), 400
    d = fn(sid)
    return jsonify(d), (200 if d.get("ok") else 400)


@app.route("/api/tutor/staende/waehlen", methods=["POST"])
def api_stand_waehlen():
    return _mit_id(dienst.stand_waehlen)


@app.route("/api/tutor/staende/loeschen", methods=["POST"])
def api_stand_loeschen():
    # POST mit id im Body statt DELETE: ein versehentlicher Browser-Aufruf
    # kann so nichts löschen.
    return _mit_id(dienst.stand_loeschen)


@app.route("/api/tutor/debug/stream")
def api_debug_stream():
    """Devtools (SSE): Momentaufnahme, Historie, dann live jedes Ereignis."""
    def erzeugen():
        snap = dienst.debug_snapshot()
        yield "data: " + json.dumps({"ts": debug._ts(), "kind": "snapshot", **snap},
                                    ensure_ascii=False) + "\n\n"
        for ev in debug.history():
            yield "data: " + json.dumps(ev, ensure_ascii=False) + "\n\n"
        q = debug.subscribe()
        try:
            while True:
                try:
                    yield "data: " + json.dumps(q.get(timeout=15), ensure_ascii=False) + "\n\n"
                except Exception:
                    yield ": keepalive\n\n"
        finally:
            debug.unsubscribe(q)
    return Response(stream_with_context(erzeugen()), content_type="text/event-stream")


# ── Stimme ─────────────────────────────────────────────────────────────

@app.route("/api/speak", methods=["POST"])
def api_speak():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "kein Text"}), 400
    wav = stimme.sprechen(text, lang=(body.get("lang") or "").strip() or None,
                          speed=float(body.get("speed", 1.0)),
                          speaker=int(body.get("speaker", 0)))
    if not wav:
        return jsonify({"error": "Stimme nicht verfügbar"}), 503
    return Response(wav, content_type="audio/wav")


@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "kein 'audio'-Feld"}), 400
    text = stimme.hoeren(request.files["audio"].read(),
                         lang=(request.form.get("lang") or "").strip() or None)
    if text.startswith("[STT"):
        return jsonify({"error": text.strip("[]"), "text": ""}), 503
    return jsonify({"text": text})


# ── Hub ────────────────────────────────────────────────────────────────

@app.route("/api/sensor/<name>", methods=["POST"])
def api_sensor(name):
    """Das Zimmer meldet „jemand ist da" (heute nur motion). Früher ging das
    an ZENTRALE; jetzt nimmt der Tutor es selbst an."""
    if name != "motion":
        return jsonify({"ok": False, "error": "unbekannter Sensor"}), 400
    return jsonify(dienst.ereignis("anwesenheit"))


@app.route("/hub/gesund")
def hub_gesund():
    return jsonify({"ok": True, "name": "tutor"})


@app.route("/hub/ereignis", methods=["POST"])
def hub_ereignis():
    """Ein Ereignis vom Hub (abonniert in app.toml)."""
    body = request.get_json(silent=True) or {}
    d = dienst.ereignis(str(body.get("name") or ""), body.get("daten") or {})
    return jsonify(d), (200 if d.get("ok") else 400)


def main():
    host = str(config.setting("host"))
    port = int(config.setting("port"))
    ordner = pfade.daten_ordner()
    print(f"[tutor] Lernstände: {ordner}", flush=True)
    if pfade.ist_alter_ort(ordner):
        print("[tutor] Hinweis: die Lernstände liegen noch im alten ZENTRALE-Ordner. "
              "Zum Umziehen den Ordner nach language-tutor/tutor/data verschieben.",
              flush=True)
    print(f"[tutor] Server auf http://{host}:{port}", flush=True)
    app.run(host=host, port=port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
