# tests/conftest.py
#
# Kein Test fasst Sashas echte Daten, Einstellungen oder Schlüssel an: alle drei
# Orte werden hier — VOR dem ersten Import von tutor — auf Wegwerf-Ordner
# gebogen (tutor/pfade.py liest sie beim Import).

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_WEG = tempfile.mkdtemp(prefix="tutor_tests_")
os.environ["TUTOR_DATEN_ORDNER"] = os.path.join(_WEG, "daten")
os.environ["TUTOR_KONFIG_ORDNER"] = os.path.join(_WEG, "konfig")
os.environ["TUTOR_SCHLUESSEL_DATEI"] = os.path.join(_WEG, "konfig", "schluessel")
os.environ["TUTOR_ZUGANG_DATEI"] = os.path.join(_WEG, "konfig", "zugang")
# Kein echtes Ollama anfragen (Tests sollen nicht vom Rechner abhängen).
os.environ["TUTOR_OLLAMA_URL"] = "http://127.0.0.1:9"
os.makedirs(os.environ["TUTOR_DATEN_ORDNER"], exist_ok=True)
