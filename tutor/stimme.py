# tutor/stimme.py
#
# Hören und Sprechen für den Tutor-Server: reicht an die Stimm-Dienste weiter
# (Whisper für Sprache → Text, TTS für Text → Sprache). Die Dienste selbst
# laufen weiter als eigene Prozesse (heute aus ZENTRALE services/, Ports
# 5050/5051); der Tutor kennt nur ihre Adresse (Einstellungen whisper_url,
# tts_url). Bis 2026-10-09 lief das über ZENTRALEs /api/speak und
# /api/transcribe.

import json
import urllib.error
import urllib.request

from . import config


def _url(name: str) -> str:
    return str(config.setting(name) or "").rstrip("/")


def gesund(name: str) -> bool:
    try:
        urllib.request.urlopen(_url(name) + "/health", timeout=2)
        return True
    except Exception:
        return False


def sprechen(text: str, lang: str = None, speed: float = 1.0, speaker: int = 0) -> bytes:
    """Text → WAV-Bytes, leer bei Fehler."""
    lang = lang or str(config.setting("default_lang"))
    koerper = json.dumps({"text": text, "lang": lang, "speed": speed,
                          "speaker": speaker}).encode("utf-8")
    try:
        req = urllib.request.Request(_url("tts_url") + "/speak", data=koerper,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except Exception as e:
        print(f"[tutor.stimme] TTS: {e}", flush=True)
        return b""


def hoeren(audio: bytes, lang: str = None) -> str:
    """WAV-Bytes → Text. Fehler → Text in eckigen Klammern ([STT …])."""
    lang = lang or str(config.setting("default_lang"))
    grenze = b"----TutorGrenze"
    koerper = (b"--" + grenze + b"\r\n"
               b'Content-Disposition: form-data; name="audio"; filename="audio.wav"\r\n'
               b"Content-Type: audio/wav\r\n\r\n" + audio + b"\r\n"
               b"--" + grenze + b"\r\n"
               b'Content-Disposition: form-data; name="lang"\r\n\r\n'
               + lang.encode() + b"\r\n--" + grenze + b"--\r\n")
    try:
        req = urllib.request.Request(
            _url("whisper_url") + "/transcribe", data=koerper, method="POST",
            headers={"Content-Type": "multipart/form-data; boundary=" + grenze.decode()})
        with urllib.request.urlopen(req, timeout=30) as r:
            return (json.loads(r.read().decode("utf-8")).get("text") or "").strip()
    except urllib.error.URLError as e:
        return f"[STT nicht erreichbar: {e.reason}]"
    except Exception as e:
        return f"[STT Fehler: {e}]"
