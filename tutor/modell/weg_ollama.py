# tutor/modell/weg_ollama.py
#
# Das lokale Ollama (seit 2026-10-09 ein eigener kleiner Weg statt ZENTRALEs
# ai.chat_stream). Kostet nichts, darum keine Buchung. Adresse und Modell aus
# den Tutor-Einstellungen ollama_url / ollama_model.

import json
import urllib.request

from .. import config
from . import schleife


def _url() -> str:
    return str(config.setting("ollama_url")).rstrip("/")


def erreichbar(timeout: float = 2.0) -> bool:
    try:
        urllib.request.urlopen(_url() + "/api/tags", timeout=timeout)
        return True
    except Exception:
        return False


def _post(pfad: str, koerper: dict, timeout: float = 120) -> dict:
    req = urllib.request.Request(_url() + pfad, data=json.dumps(koerper).encode("utf-8"),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fahren(verlauf, *, modell, system, tools, ausfuehren, senden=None):
    msgs = [{"role": "system", "content": system}]
    msgs += [{"role": m["role"], "content": m["content"]} for m in verlauf or []
             if m.get("role") in ("user", "assistant") and m.get("content")]
    adapter = Adapter(modell or str(config.setting("ollama_model")), msgs,
                      list(tools or []), senden or _post)
    yield from schleife.laufen(adapter, ausfuehren=ausfuehren, name="Ollama")


class Adapter:
    def __init__(self, modell, msgs, tools, senden):
        self.modell, self.msgs, self.tools, self.senden = modell, msgs, tools, senden

    def runde(self):
        koerper = {"model": self.modell, "messages": self.msgs, "stream": False,
                   "think": False}
        if self.tools:
            koerper["tools"] = self.tools
        antwort = self.senden("/api/chat", koerper)
        msg = antwort.get("message") or {}
        calls = []
        for i, tc in enumerate(msg.get("tool_calls") or []):
            fn = tc.get("function") or {}
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except ValueError:
                    args = {}
            calls.append((f"c{i}", fn.get("name", ""), args))
        return schleife.Runde(msg.get("content") or "", calls, roh=msg)
        yield  # noqa: unreachable — macht runde() zum Generator

    def assistent_anhaengen(self, runde):
        self.msgs.append(runde.roh)

    def ergebnisse_anhaengen(self, ergebnisse):
        for _cid, text, _ in ergebnisse:
            self.msgs.append({"role": "tool", "content": str(text)})
