# tutor/ — der Sprach-Tutor (Persona-Portal).
#
# EIGENES PROGRAMM (seit 2026-10-09 eigenes Repo „language-tutor"; vorher
# wohnte es in ZENTRALE mit). Es ist die erste App nach ZENTRALEs Hub-Bauplan:
# eigener Prozess (tutor/server.py), eigener Schlüssel und eigenes Budget
# (tutor/modell/), eigene Einstellungen (tutor/config.py). Was die App vom Hub
# will, steht in app.toml.
#
# ── Die eine Regel ──────────────────────────────────────────────────────
# Kein Import außerhalb dieses Repos — weder ZENTRALE-Kern noch sonst etwas
# von dort (tests/test_tutor_grenze.py). Mit dem Hub redet der Tutor nur über
# HTTP: er nimmt Ereignisse an (POST /hub/ereignis), mehr nicht.

# ── Sprache = Ordner (tutor/langs/<code>/) ──────────────────────────────
# Der Tutor ist ein FRAMEWORK, kein Chinesisch-Tutor. Alles, was eine Sprache
# ausmacht, liegt in ihrem Paket: Prompt (in der ZIELSPRACHE), Tool-Beschriftung,
# Register-Leiter, Landes-Seeds. tools.py/session.py sind sprach-NEUTRAL und
# lösen pro Aufruf über die aktive Sprache auf (session.active_lang()).
# Eine Sprache dazubauen = einen Ordner anlegen. Siehe tutor/langs/__init__.py.
#
# ── Sandbox (Invariante, nie aufweichen) ────────────────────────────────
# Die Persona-Stores (tutor/data/<lang>/persona_mem.json) und Sashas Core-KI-
# Memory (data/ai_graph.json) fassen sich NIE an. Tool-Zugriffe laufen über die
# Allowlist in tutor/tools.py (_ALLOWED).
#
# ── Secrets ─────────────────────────────────────────────────────────────
# Im Repo liegt KEIN Schlüssel. Der eigene Schlüssel steht in
# ~/.config/language-tutor/schluessel (tutor/modell/schluessel.py).
