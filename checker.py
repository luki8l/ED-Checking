#!/usr/bin/env python3
"""
Verfügbarkeits-Checker für coachingbyed.de
GitHub Actions Version – läuft einmalig, kein Loop nötig.
GitHub Actions triggert das Script automatisch alle X Minuten.
"""

import requests
import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

URL = "https://www.coachingbyed.de/jetzt-buchen/"
SOLD_OUT_MARKER = "Alle Plätze sind ausgebucht"
STATE_FILE = ".state/notified"

# Wird aus GitHub Secrets geladen (nicht hier eintragen!)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
EMAIL_TO  = os.environ["EMAIL_TO"]


def is_notified() -> bool:
    return os.path.isfile(STATE_FILE)


def set_notified():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(datetime.now().isoformat())


def clear_notified():
    if os.path.isfile(STATE_FILE):
        os.remove(STATE_FILE)


def check_availability() -> bool:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AvailabilityChecker/1.0)"}
    resp = requests.get(URL, headers=headers, timeout=20)
    resp.raise_for_status()
    return SOLD_OUT_MARKER not in resp.text


def send_email():
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🎉 Coaching-Platz verfügbar bei ED Coaching!"
    msg["From"]    = SMTP_USER
    msg["To"]      = EMAIL_TO

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    body_text = f"""
Hallo!

Auf {URL} sind wieder Coaching-Plätze verfügbar!

👉 Jetzt schnell buchen: {URL}

(Automatische Benachrichtigung vom {now})
"""
    body_html = f"""
<html><body style="font-family:sans-serif;max-width:500px;margin:40px auto;">
  <h2 style="color:#2ecc71">🎉 Coaching-Plätze sind wieder frei!</h2>
  <p>Auf <a href="{URL}">coachingbyed.de</a> sind wieder Plätze verfügbar.</p>
  <p>
    <a href="{URL}" style="background:#2ecc71;color:white;padding:12px 24px;
       text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block;">
      Jetzt buchen →
    </a>
  </p>
  <p style="color:#999;font-size:12px;">Automatische Benachrichtigung vom {now}</p>
</body></html>
"""
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html",  "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())

    print(f"✅ E-Mail gesendet an {EMAIL_TO}")


def main():
    print(f"🔍 Prüfe {URL} ...")
    try:
        available = check_availability()
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Seite: {e}")
        sys.exit(1)

    if available:
        if is_notified():
            print("🎉 Plätze verfügbar – E-Mail bereits gesendet, kein erneuter Versand.")
            sys.exit(0)
        print("🎉 PLÄTZE VERFÜGBAR! Sende E-Mail...")
        try:
            send_email()
            set_notified()
        except Exception as e:
            print(f"❌ Fehler beim Senden der E-Mail: {e}")
            sys.exit(1)
    else:
        print("😴 Noch ausgebucht.")
        clear_notified()
    sys.exit(0)


if __name__ == "__main__":
    main()
