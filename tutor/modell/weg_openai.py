# tutor/modell/weg_openai.py
#
# Der OpenAI-kompatible Dialekt (Qwen, OpenAI, Mistral, Gemini, …). Portiert
# aus ZENTRALE core/cloud_openai.py (2026-10-09), nur der Tutor-Teil.

import json

from . import kosten, schleife


def _client(base_url: str, schluessel: str):
    from openai import OpenAI             # erst laden, wenn wirklich gebraucht
    return OpenAI(base_url=base_url, api_key=schluessel)


def nachrichten(system: str, verlauf: list) -> list:
    raus = [{"role": "system", "content": system}]
    raus += [{"role": m["role"], "content": m["content"]} for m in verlauf or []
             if m.get("role") in ("user", "assistant") and m.get("content")]
    if not any(m["role"] == "user" for m in raus):
        raus.append({"role": "user", "content": "(…)"})
    return raus


def fahren(verlauf, *, modell, system, tools, ausfuehren, schluessel, base_url,
           max_tokens=140, temperatur=0.4, client=None):
    adapter = Adapter(client or _client(base_url, schluessel), modell,
                      nachrichten(system, verlauf), list(tools or []),
                      max_tokens=max_tokens, temperatur=temperatur)
    yield from schleife.laufen(adapter, ausfuehren=ausfuehren)


class Adapter:
    def __init__(self, client, modell, msgs, tools, max_tokens, temperatur):
        self.client, self.modell, self.msgs, self.tools = client, modell, msgs, tools
        self.max_tokens = int(max_tokens or 140)
        self.temperatur = 0.4 if temperatur is None else float(temperatur)

    def runde(self):
        text, calls_roh, verbrauch = [], {}, None
        strom = self.client.chat.completions.create(
            model=self.modell, messages=self.msgs, tools=self.tools or None,
            stream=True, temperature=self.temperatur, max_tokens=self.max_tokens,
            stream_options={"include_usage": True})
        for chunk in strom:
            if getattr(chunk, "usage", None):
                verbrauch = chunk.usage
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            denk = getattr(delta, "reasoning_content", None)
            if denk:
                yield {"reflect": denk}
            if getattr(delta, "content", None):
                text.append(delta.content)
            for tc in (getattr(delta, "tool_calls", None) or []):
                slot = calls_roh.setdefault(tc.index, {"id": None, "name": "", "args": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        slot["name"] = tc.function.name
                    if tc.function.arguments:
                        slot["args"] += tc.function.arguments
        if verbrauch is not None:
            rein = int(getattr(verbrauch, "prompt_tokens", 0) or 0)
            det = getattr(verbrauch, "prompt_tokens_details", None)
            gecacht = int(getattr(det, "cached_tokens", 0) or 0) if det else 0
            kosten.buchen(self.modell, rein=max(rein - gecacht, 0),
                          raus=int(getattr(verbrauch, "completion_tokens", 0) or 0),
                          cache_lesen=gecacht)
        calls = []
        for s in calls_roh.values():
            try:
                args = json.loads(s["args"] or "{}")
            except ValueError:
                args = {}
            calls.append((s["id"], s["name"], args))
        return schleife.Runde("".join(text), calls, roh=list(calls_roh.values()))

    def assistent_anhaengen(self, runde):
        self.msgs.append({"role": "assistant", "content": runde.text or None,
                          "tool_calls": [{"id": s["id"], "type": "function",
                                          "function": {"name": s["name"],
                                                       "arguments": s["args"] or "{}"}}
                                         for s in runde.roh]})

    def ergebnisse_anhaengen(self, ergebnisse):
        for cid, text, _ in ergebnisse:
            self.msgs.append({"role": "tool", "tool_call_id": cid, "content": str(text)})
