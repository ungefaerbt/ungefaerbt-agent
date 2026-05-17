"""
email_report.py
---------------
Letzter Pipeline-Schritt: Sendet eine HTML-Mail mit allen Social-Kandidaten.

Ausfuehren:
    python email_report.py final_social_candidates.json
"""

import base64
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import barometer_png as _barometer

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("email_report")

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

FARBE_BG        = "#1C1814"
FARBE_CARD      = "#252018"
FARBE_GOLD      = "#C8A96E"
FARBE_TEXT      = "#F0EBE0"
FARBE_MUTED     = "#9E9589"
FARBE_BORDER    = "#3A3428"
FARBE_CONTRAST  = "#2A2010"

# ---------------------------------------------------------------------------
# HTML-Bausteine
# ---------------------------------------------------------------------------

def _esc(text):
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _spektren_html(story):
    aktiv_roh  = story.get("political_leaning", "") or ""
    aktiv = [s.strip() for s in aktiv_roh.split(",") if s.strip()]
    still = story.get("silent_spectrums") or []
    if isinstance(still, str):
        still = [s.strip() for s in still.split(",") if s.strip()]

    teile = []
    for s in aktiv:
        teile.append(
            f'<span style="color:{FARBE_GOLD};margin-right:10px;">✓ {_esc(s)}</span>'
        )
    for s in still:
        teile.append(
            f'<span style="color:{FARBE_MUTED};margin-right:10px;text-decoration:line-through;">'
            f'✗ {_esc(s)}</span>'
        )
    if not teile:
        return ""
    return (
        f'<p style="margin:6px 0;font-size:13px;line-height:1.7;">'
        + "".join(teile)
        + "</p>"
    )


def _kontrast_html(story):
    if not story.get("has_contrast"):
        return ""

    paare = story.get("contrast_pairs") or []
    contrast_type = _esc(story.get("contrast_type", ""))

    paare_html = ""
    for paar in paare:
        src_a  = _esc(paar.get("source_a", ""))
        hl_a   = _esc(paar.get("headline_a", ""))
        lean_a = _esc(paar.get("political_leaning_a", ""))
        src_b  = _esc(paar.get("source_b", ""))
        hl_b   = _esc(paar.get("headline_b", ""))
        lean_b = _esc(paar.get("political_leaning_b", ""))
        erkl   = _esc(paar.get("explanation", ""))

        paare_html += f"""
        <div style="margin:10px 0;padding:10px;border-left:3px solid {FARBE_GOLD};
                    background:{FARBE_BG};border-radius:4px;">
          <p style="margin:0 0 4px;font-size:13px;color:{FARBE_MUTED};">
            <strong style="color:{FARBE_TEXT};">{src_a}</strong>
            {f'<span> [{lean_a}]</span>' if lean_a else ''}
          </p>
          <p style="margin:0 0 8px;font-size:14px;color:{FARBE_TEXT};">"{hl_a}"</p>
          <p style="margin:0 0 4px;font-size:13px;color:{FARBE_MUTED};">
            <strong style="color:{FARBE_TEXT};">{src_b}</strong>
            {f'<span> [{lean_b}]</span>' if lean_b else ''}
          </p>
          <p style="margin:0 0 8px;font-size:14px;color:{FARBE_TEXT};">"{hl_b}"</p>
          {f'<p style="margin:0;font-size:12px;color:{FARBE_MUTED};">{erkl}</p>' if erkl else ''}
        </div>"""

    return f"""
    <div style="margin:14px 0;padding:12px;background:{FARBE_CONTRAST};border-radius:6px;
                border:1px solid {FARBE_GOLD}33;">
      <p style="margin:0 0 8px;font-size:12px;font-weight:600;letter-spacing:.05em;
                text-transform:uppercase;color:{FARBE_GOLD};">
        Headline-Kontrast · {contrast_type}
        · Score: {story.get('contrast_score', 0)}
      </p>
      {paare_html}
    </div>"""


def _barometer_html(story) -> str:
    try:
        pfad = _barometer.barometer_erstellen(story)
        b64  = base64.b64encode(pfad.read_bytes()).decode()
        return (
            f'<div style="margin:12px 0;">'
            f'<img src="data:image/png;base64,{b64}" '
            f'width="560" height="22" style="display:block;border-radius:3px;" '
            f'alt="Spektrum-Barometer"/>'
            f'</div>'
        )
    except Exception:
        return ""


def _source_headlines_html(post_data: dict) -> str:
    eintraege = post_data.get("source_headlines") or []
    if not eintraege:
        return ""
    zeilen = ""
    for e in eintraege:
        src   = _esc(e.get("source", ""))
        hl    = _esc(e.get("headline", ""))
        lean  = _esc(e.get("leaning", ""))
        lean_tag = f' <span style="font-size:11px;">[{lean}]</span>' if lean else ""
        zeilen += (
            f'<p style="margin:3px 0;font-size:12px;color:{FARBE_MUTED};">'
            f'<span style="color:{FARBE_TEXT};">{src}</span>{lean_tag}'
            f': "{hl}"</p>'
        )
    return f"""
    <div style="margin:14px 0;">
      <p style="margin:0 0 6px;font-size:11px;font-weight:600;letter-spacing:.05em;
                text-transform:uppercase;color:{FARBE_MUTED};">Originaltitel (Auswahl)</p>
      {zeilen}
    </div>"""


def _perspektiven_html(post_data: dict) -> str:
    left  = _esc(post_data.get("left_perspective", ""))
    right = _esc(post_data.get("right_perspective", ""))
    if not left and not right:
        return ""
    return f"""
    <div style="margin:14px 0;display:flex;gap:10px;">
      <div style="flex:1;padding:10px;background:{FARBE_BG};border-left:3px solid #7BAE7F;border-radius:4px;">
        <p style="margin:0 0 4px;font-size:11px;font-weight:600;letter-spacing:.05em;
                  text-transform:uppercase;color:#7BAE7F;">Links</p>
        <p style="margin:0;font-size:13px;color:{FARBE_TEXT};">{left}</p>
      </div>
      <div style="flex:1;padding:10px;background:{FARBE_BG};border-left:3px solid #E8A87C;border-radius:4px;">
        <p style="margin:0 0 4px;font-size:11px;font-weight:600;letter-spacing:.05em;
                  text-transform:uppercase;color:#E8A87C;">Rechts</p>
        <p style="margin:0;font-size:13px;color:{FARBE_TEXT};">{right}</p>
      </div>
    </div>"""


def _quellartikel_html(story):
    quellen = story.get("source_articles") or []
    if not quellen:
        return ""

    zeilen = ""
    for a in quellen:
        src   = _esc(a.get("source", ""))
        lean  = _esc(a.get("political_leaning", ""))
        hl    = _esc(a.get("headline", ""))
        link  = a.get("link", "")
        label = f"{src}{f' [{lean}]' if lean else ''}"

        if link:
            zeilen += (
                f'<p style="margin:4px 0;font-size:12px;color:{FARBE_MUTED};">'
                f'<span style="color:{FARBE_TEXT};">{label}:</span> '
                f'<a href="{_esc(link)}" style="color:{FARBE_GOLD};text-decoration:none;">"{hl}"</a>'
                f'</p>'
            )
        else:
            zeilen += (
                f'<p style="margin:4px 0;font-size:12px;color:{FARBE_MUTED};">'
                f'<span style="color:{FARBE_TEXT};">{label}:</span> "{hl}"'
                f'</p>'
            )

    return f"""
    <div style="margin:14px 0;">
      <p style="margin:0 0 6px;font-size:11px;font-weight:600;letter-spacing:.05em;
                text-transform:uppercase;color:{FARBE_MUTED};">Quellartikel</p>
      {zeilen}
    </div>"""


def _story_block_html(rang, story, post_data=None):
    headline   = _esc(story.get("headline", "–"))
    summary    = _esc(story.get("summary", ""))
    kategorie  = _esc(story.get("category", ""))
    barometer  = _esc(story.get("blindspot_label", ""))
    bs_score   = story.get("blindspot_score", "–")
    prio_score = story.get("social_priority_score", story.get("social_post_score", "–"))
    angle      = _esc(story.get("social_angle", ""))
    reason     = _esc(story.get("social_reason", ""))

    fmt = (story.get("recommended_social_format")
           or story.get("suggested_social_format") or "–")
    fmt = _esc(fmt.replace("_", " "))

    meta_teile = [t for t in [kategorie, barometer] if t]
    meta_str   = " · ".join(meta_teile)
    if bs_score != "–":
        meta_str += f" · Blindspot {bs_score}"

    return f"""
  <div style="background:{FARBE_CARD};border:1px solid {FARBE_BORDER};border-radius:10px;
              padding:18px;margin-bottom:20px;">

    <!-- Rang + Score -->
    <p style="margin:0 0 10px;font-size:12px;color:{FARBE_MUTED};">
      <span style="background:{FARBE_GOLD};color:{FARBE_BG};font-weight:700;
                   padding:2px 8px;border-radius:12px;margin-right:8px;">#{rang}</span>
      <span style="color:{FARBE_GOLD};font-weight:600;">Score {prio_score}</span>
    </p>

    <!-- Headline -->
    <h2 style="margin:0 0 8px;font-size:18px;font-weight:700;line-height:1.35;
               color:{FARBE_TEXT};">{headline}</h2>

    <!-- Meta -->
    {f'<p style="margin:0 0 10px;font-size:12px;color:{FARBE_MUTED};">{meta_str}</p>' if meta_str else ''}

    <!-- Summary -->
    {f'<p style="margin:0 0 12px;font-size:14px;line-height:1.6;color:{FARBE_TEXT};">{summary}</p>' if summary else ''}

    <!-- Spektren -->
    {_spektren_html(story)}

    <!-- Format -->
    <p style="margin:10px 0 4px;font-size:12px;color:{FARBE_MUTED};">
      Format: <span style="color:{FARBE_GOLD};">{fmt}</span>
    </p>

    <!-- Angle + Reason -->
    {f'<p style="margin:4px 0;font-size:13px;color:{FARBE_TEXT};">{angle}</p>' if angle else ''}
    {f'<p style="margin:4px 0 0;font-size:12px;color:{FARBE_MUTED};">{reason}</p>' if reason else ''}

    <!-- Barometer -->
    {_barometer_html(story)}

    <!-- Kontrast -->
    {_kontrast_html(story)}

    <!-- Perspektiven (nur bei a_sagt_x_b_sagt_y) -->
    {_perspektiven_html(post_data) if post_data else ""}

    <!-- Originaltitel (source_headlines) -->
    {_source_headlines_html(post_data) if post_data else ""}

    <!-- Quellartikel -->
    {_quellartikel_html(story)}

  </div>"""


def _post_lookup_laden() -> dict:
    pfad = Path(__file__).parent / "output" / "social_pack_output.json"
    if not pfad.exists():
        return {}
    try:
        with open(pfad, encoding="utf-8") as f:
            posts = json.load(f)
        return {p["headline"]: p for p in posts if p.get("headline")}
    except Exception:
        return {}


def html_erstellen(kandidaten):
    jetzt = datetime.now()
    datum_str = jetzt.strftime("%-d. %B %Y") if sys.platform != "win32" else jetzt.strftime("%d. %B %Y").lstrip("0")
    anzahl = len(kandidaten)
    betreff = f"ungefärbt — {anzahl} Social-Kandidaten | {datum_str}"

    post_lookup = _post_lookup_laden()

    if not kandidaten:
        inhalt_html = f"""
      <div style="text-align:center;padding:40px 20px;">
        <p style="font-size:16px;color:{FARBE_MUTED};">
          Heute keine Social-Kandidaten gefunden.
        </p>
      </div>"""
    else:
        inhalt_html = "".join(
            _story_block_html(i + 1, s, post_data=post_lookup.get(s.get("headline", "")))
            for i, s in enumerate(kandidaten)
        )

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(betreff)}</title>
</head>
<body style="margin:0;padding:0;background:{FARBE_BG};font-family:system-ui,-apple-system,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:16px;">

  <!-- Header -->
  <div style="text-align:center;padding:24px 0 20px;">
    <h1 style="margin:0;font-size:22px;font-weight:800;letter-spacing:.04em;
               color:{FARBE_GOLD};">ungefärbt</h1>
    <p style="margin:6px 0 0;font-size:13px;color:{FARBE_MUTED};">
      {_esc(datum_str)} · {anzahl} Social-Kandidaten
    </p>
  </div>

  <!-- Stories -->
  {inhalt_html}

  <!-- Footer -->
  <div style="border-top:1px solid {FARBE_BORDER};margin-top:24px;padding-top:16px;
              text-align:center;">
    <p style="margin:0;font-size:11px;color:{FARBE_MUTED};">
      Generiert von ungefärbt pipeline · {_esc(jetzt.strftime('%d.%m.%Y %H:%M'))}
    </p>
  </div>

</div>
</body>
</html>"""

    return betreff, html


# ---------------------------------------------------------------------------
# Mail senden
# ---------------------------------------------------------------------------

def mail_senden(betreff, html_body, sender, recipient, api_key, attachments=None):
    import resend
    resend.api_key = api_key
    payload = {
        "from": sender,
        "to": recipient,
        "subject": betreff,
        "html": html_body,
    }
    if attachments:
        payload["attachments"] = attachments
    resend.Emails.send(payload)


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Verwendung: python email_report.py final_social_candidates.json")
        sys.exit(1)

    input_pfad = sys.argv[1]
    log.info("email_report gestartet: %s", input_pfad)

    # .env laden
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    sender    = os.getenv("EMAIL_SENDER")
    recipient = os.getenv("EMAIL_RECIPIENT")
    api_key   = os.getenv("RESEND_API_KEY")

    fehlend = [n for n, v in [
        ("EMAIL_SENDER", sender),
        ("EMAIL_RECIPIENT", recipient),
        ("RESEND_API_KEY", api_key),
    ] if not v]
    if fehlend:
        for name in fehlend:
            log.error("Umgebungsvariable fehlt: %s", name)
        sys.exit(1)

    # Kandidaten laden
    try:
        with open(input_pfad, "r", encoding="utf-8") as f:
            kandidaten = json.load(f)
        if not isinstance(kandidaten, list):
            kandidaten = []
    except FileNotFoundError:
        log.warning("Datei nicht gefunden: %s — sende leere Mail.", input_pfad)
        kandidaten = []
    except json.JSONDecodeError as e:
        log.error("JSON-Fehler in '%s': %s", input_pfad, e)
        sys.exit(1)

    log.info("%s Social-Kandidaten geladen.", len(kandidaten))

    # Barometer-PNGs generieren und als Anhänge sammeln
    attachments = []
    for story in kandidaten:
        try:
            pfad = _barometer.barometer_erstellen(story)
            attachments.append({
                "filename": pfad.name,
                "content":  list(pfad.read_bytes()),
            })
        except Exception as e:
            log.warning("Barometer-Fehler für '%s': %s", story.get("headline", "?")[:50], e)

    log.info("%s Barometer-PNGs als Anhang vorbereitet.", len(attachments))

    # HTML erstellen
    betreff, html_body = html_erstellen(kandidaten)

    # Mail senden
    log.info("Sende Mail an %s ...", recipient)
    try:
        mail_senden(betreff, html_body, sender, recipient, api_key, attachments=attachments or None)
        log.info("Mail erfolgreich gesendet: %s", betreff)
    except Exception as e:
        log.error("Fehler beim Mailversand via Resend: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
