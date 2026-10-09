# tutor/modell/weg_anthropic.py
#
# Der Anthropic-Dialekt (tool_use-Blöcke). Portiert aus ZENTRALE core/cloud.py
# (2026-10-09), nur der Tutor-Teil: der System-Prompt ist der des Tutors, ganz
# und allein; nichts aus Sashas Assistenten kommt dazu.

from . import kosten, schleife

# Adaptives Denken nur auf Modellen, die es können (Haiku antwortet sonst 400).
_DENKT_ADAPTIV = ("claude-opus-5", "claude-sonnet-5", "claude-opus-4.8")


def _client(schluessel: str):
    import anthropic                     # erst laden, wenn wirklich gebraucht
    return anthropic.Anthropic(api_key=schluessel)


def werkzeuge_umwandeln(openai_tools: list) -> list:
    """OpenAI-Schema → Anthropic-Schema (Reihenfolge bleibt: Cache-Präfix)."""
    raus = []
    for t in openai_tools or []:
        fn = t.get("function", t)
        raus.append({"name": fn["name"], "description": fn.get("description", ""),
                     "input_schema": fn.get("parameters",
                                            {"type": "object", "properties": {}})})
    return raus


def nachrichten(verlauf: list) -> list:
    raus = [{"role": m["role"], "content": m["content"]} for m in verlauf or []
            if m.get("role") in ("user", "assistant") and m.get("content")]
    if not raus or raus[0]["role"] != "user":
        raus.insert(0, {"role": "user", "content": "(…)"})
    return raus


def fahren(verlauf, *, modell, system, tools, ausfuehren, schluessel,
           max_tokens=2000, effort="low", client=None):
    adapter = Adapter(client or _client(schluessel), modell,
                      [{"type": "text", "text": system,
                        "cache_control": {"type": "ephemeral"}}],
                      nachrichten(verlauf), werkzeuge_umwandeln(tools),
                      max_tokens=max_tokens, effort=effort)
    yield from schleife.laufen(adapter, ausfuehren=ausfuehren)


class Adapter:
    def __init__(self, client, modell, system, msgs, tools, max_tokens, effort):
        self.client, self.modell = client, modell
        self.system, self.msgs, self.tools = system, msgs, tools
        self.max_tokens, self.effort = int(max_tokens or 2000), effort or "low"

    def _denken(self) -> dict:
        if not any(self.modell.startswith(m) for m in _DENKT_ADAPTIV):
            return {}
        return {"thinking": {"type": "adaptive", "display": "summarized"},
                "output_config": {"effort": self.effort}}

    def runde(self):
        text = []
        extra = {"tools": self.tools} if self.tools else {}
        with self.client.messages.stream(
                model=self.modell, max_tokens=self.max_tokens,
                system=self.system, messages=self.msgs,
                **extra, **self._denken()) as strom:
            for ev in strom:
                if getattr(ev, "type", "") != "content_block_delta":
                    continue
                d = ev.delta
                if d.type == "thinking_delta":
                    yield {"reflect": d.thinking}
                elif d.type == "text_delta":
                    text.append(d.text)
            final = strom.get_final_message()
        u = getattr(final, "usage", None)
        if u is not None:
            kosten.buchen(self.modell,
                          rein=int(getattr(u, "input_tokens", 0) or 0),
                          raus=int(getattr(u, "output_tokens", 0) or 0),
                          cache_lesen=int(getattr(u, "cache_read_input_tokens", 0) or 0),
                          cache_schreiben=int(getattr(u, "cache_creation_input_tokens", 0) or 0))
        if final.stop_reason == "refusal":
            raise schleife.Abbruch("Der Anbieter hat diese Anfrage abgelehnt.")
        calls = []
        if final.stop_reason == "tool_use":
            calls = [(b.id, b.name, dict(b.input or {})) for b in final.content
                     if getattr(b, "type", None) == "tool_use"]
        if not text:
            text = [getattr(b, "text", "") for b in final.content
                    if getattr(b, "type", None) == "text"]
        return schleife.Runde("".join(text), calls, roh=final)

    def assistent_anhaengen(self, runde):
        self.msgs.append({"role": "assistant", "content": runde.roh.content})

    def ergebnisse_anhaengen(self, ergebnisse):
        bloecke = []
        for cid, text, ist_fehler in ergebnisse:
            b = {"type": "tool_result", "tool_use_id": cid, "content": str(text)}
            if ist_fehler:
                b["is_error"] = True
            bloecke.append(b)
        self.msgs.append({"role": "user", "content": bloecke})
