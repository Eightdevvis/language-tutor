# tutor/zugang.py
#
# Der Zugangsschlüssel des Tutor-Servers — beide Seiten in einer Datei.
#
# Der Server lauscht normalerweise nur auf diesem Rechner (host 127.0.0.1).
# Hängt das Zimmer an der Wand (Pi) und der Server läuft am PC, muss er im
# Heimnetz lauschen — dann darf nicht jeder im Netz mit Lucía reden oder
# Lernstände löschen. Darum: Anfragen von außerhalb dieses Rechners brauchen
# den Schlüssel aus ~/.config/language-tutor/zugang (Env TUTOR_ZUGANG_DATEI),
# auf beiden Rechnern dieselbe Zeile. Ohne Datei werden fremde Anfragen
# abgewiesen.
#
# Bis 2026-10-09 lud das Zimmer dafür den Zugangs-Klienten aus ZENTRALE
# per Dateipfad; das ist hier dieselbe Idee, aber im eigenen Repo (eine App
# lädt keinen Hub-Code). Nur Standardbibliothek: fährt mit dem Zimmer auf den Pi.

import hmac
import os
import urllib.request


def datei() -> str:
    return os.path.expanduser(os.environ.get("TUTOR_ZUGANG_DATEI")
                              or "~/.config/language-tutor/zugang")


def schluessel():
    try:
        with open(datei(), encoding="ascii") as f:
            k = f.read().strip()
    except (OSError, UnicodeDecodeError):
        return None
    return k or None


_LOKAL = ("127.0.0.1", "::1", "localhost")


def erlaubt(adresse: str, kopf: str) -> bool:
    """Server-Seite: darf diese Anfrage rein?"""
    if (adresse or "") in _LOKAL:
        return True
    k = schluessel()
    if not k:
        return False
    return hmac.compare_digest((kopf or "").encode(), ("Bearer " + k).encode())


class _Kopf(urllib.request.BaseHandler):
    handler_order = 100

    def __init__(self, basis: str):
        self.basis = basis.rstrip("/") + "/"

    def http_request(self, req):
        if (req.full_url + "/").startswith(self.basis) and not req.has_header("Authorization"):
            k = schluessel()
            if k:
                req.add_unredirected_header("Authorization", f"Bearer {k}")
        return req

    https_request = http_request


def einrichten(basis_url: str) -> None:
    """Zimmer-Seite: ab jetzt trägt jede urllib-Anfrage an basis_url den
    Schlüssel (falls einer da ist)."""
    urllib.request.install_opener(urllib.request.build_opener(_Kopf(basis_url)))
