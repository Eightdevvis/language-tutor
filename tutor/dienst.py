# tutor/dienst.py
#
# Was der Tutor-Server nach außen anbietet — ohne HTTP (das macht server.py).
#
# Bis 2026-10-09 stand diese Logik in ZENTRALE (core/tutor_port.py): ZENTRALE
# griff per Import in den Tutor, prüfte seine Drossel, baute Status und
# Einstellungen fürs Zimmer. Seit der Tutor ein eigenes Programm ist, gehört
# das ihm. Es gibt keine ZENTRALE-Drossel mehr davor; der Tutor hat seinen
# eigenen Schlüssel und sein eigenes Budget (tutor/modell/).

from . import anbieter, config, langs, session, staende, tools

OPTIKEN = ("pixel", "alt")
MUTTERSPRACHEN = ["en", "de", "es", "zh", "fr", "ru", "ar"]


def _sicher(fn, standard):
    try:
        return fn()
    except Exception:
        return standard


def status() -> dict:
    grund = _sicher(session.unavailable_reason, "Tutor kaputt (siehe Log)")
    return {
        "present":         True,
        "active":          _sicher(session.is_active, False),
        "available":       not grund,
        "reason":          grund,
        "privacy_warning": _sicher(session.privacy_notice, None),
    }


def optik() -> str:
    v = str(config.setting("tutor_optik") or "pixel").strip().lower()
    return v if v in OPTIKEN else "pixel"


def einstellungen(changes: dict = None, persist: bool = False) -> dict:
    """Liest (und ändert optional) die Einstellungen fürs Zimmer."""
    if changes and "lang" in changes:
        # Sprache = Spielstand (seit 2026-09-17).
        return {"present": True, "error": "Sprache ist keine Einstellung mehr — "
                                          "sie gehört zum Spielstand"}
    for k in ("provider", "model", "history_window", "native"):
        if changes and k in changes:
            config.set_override(k, changes[k], persist=persist)
    if changes and changes.get("optik") in OPTIKEN:
        config.set_override("tutor_optik", changes["optik"], persist=persist)

    prof, pname, _prov, model = session._resolve()
    return {
        "present":        True,
        "lang":           session.active_lang(),
        "native":         config.setting("native"),
        "native_names":   prof.get("native_names") or {},
        "natives":        MUTTERSPRACHEN,
        "lang_name":      prof["name"],
        "persona_name":   prof.get("persona_name", prof["name"]),
        "country":        prof.get("country", ""),
        "avatar":         prof.get("avatar") or "lucia",
        "optik":          optik(),
        "provider":       pname,
        "model":          model,
        "trains_on_data": anbieter.trains_on_data(pname),
        "providers":      anbieter.liste(),
        # fertige Sprachen zuerst, dann alphabetisch
        "langs": [
            {"code": c, "name": p["name"], "enabled": p.get("enabled"),
             "persona_name": p.get("persona_name", p["name"]),
             "country": p.get("country", ""), "reading": p.get("reading")}
            for c, p in sorted(langs.PROFILES.items(),
                               key=lambda kv: (not kv[1].get("enabled"), kv[0]))
        ],
    }


# ── Drill (deterministisch, kein Modell) ────────────────────────────────

def assessment() -> dict:
    try:
        lang = session.active_lang()
        got, total = tools.core_coverage(lang)
        return {
            "present":  True, "lang": lang,
            "mode":     "assessment" if tools.assessment_active(lang) else "room",
            "got":      got, "total": total,
            "ratio":    round(got / total, 3) if total else 0.0,
            "unlocked": tools.core_graduated(lang),
            "speed":    tools.tts_speed_for(lang),
            "queue":    tools.assessment_queue(lang),
            "game":     tools.game_state(lang),
        }
    except Exception as e:
        return {"present": True, "error": str(e), "queue": []}


def assessment_answer(word: str, result: str) -> dict:
    try:
        return tools.assessment_answer(session.active_lang(), word, result)
    except Exception as e:
        return {"error": str(e)}


def debug_snapshot() -> dict:
    try:
        return tools.debug_snapshot(session.active_lang())
    except Exception as e:
        return {"error": str(e)}


# ── Spielstände ────────────────────────────────────────────────────────

def _wurzel():
    return tools._DATA_ROOT


def staende_liste() -> dict:
    try:
        root = _wurzel()
        return {"present": True, "aktiv": staende.aktiv(root),
                "levels": staende.LEVEL_NAMEN, "staende": staende.liste(root)}
    except Exception as e:
        return {"present": True, "error": str(e), "staende": [], "aktiv": None}


def _sitzung_beenden():
    """Laufende Sitzung beenden — sie gehört zum alten Stand (sonst redet
    Lucía mit den Erinnerungen des vorigen Stands weiter)."""
    _sicher(session.deactivate, None)


def stand_anlegen(name: str = None, lang: str = None, level: int = 0) -> dict:
    try:
        root = _wurzel()
        if lang not in langs.enabled():
            return {"ok": False, "error": "unbekannte oder nicht fertige Sprache: %s" % lang}
        with staende.stand_lock:
            _sitzung_beenden()
            sid = staende.anlegen(root, name, lang=lang, level=level)
            staende.waehlen(root, sid)
            tools.level_anwenden(lang, int(level or 0))
        return {"ok": True, "aktiv": sid, "staende": staende.liste(root)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def stand_waehlen(sid: str) -> dict:
    try:
        root = _wurzel()
        with staende.stand_lock:
            _sitzung_beenden()
            if not staende.waehlen(root, sid):
                return {"ok": False, "error": "unbekannter Spielstand: %s" % sid}
        return {"ok": True, "aktiv": sid, "staende": staende.liste(root)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def stand_loeschen(sid: str) -> dict:
    try:
        root = _wurzel()
        with staende.stand_lock:
            if staende.aktiv(root) == sid:
                _sitzung_beenden()
            if not staende.loeschen(root, sid):
                return {"ok": False, "error": "unbekannter Spielstand: %s" % sid}
        return {"ok": True, "aktiv": staende.aktiv(root), "staende": staende.liste(root)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Ereignisse vom Hub ─────────────────────────────────────────────────

def ereignis(name: str, daten: dict = None) -> dict:
    """Ein Ereignis, das der Hub (ZENTRALE) schickt, weil der Tutor es in
    app.toml abonniert hat. Heute nur „anwesenheit" (jemand ist im Raum)."""
    if name == "anwesenheit":
        if str(config.setting("presence_react")) == "0":
            return {"ok": True, "reagiert": False, "grund": "presence_react=0"}
        return {"ok": True, "reagiert": bool(_sicher(session.presence_ping, False))}
    return {"ok": False, "error": "Ereignis nicht abonniert: %s" % name}
