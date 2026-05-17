"""
barometer_png.py
----------------
Generiert ein Spektrum-Barometer-Bild (1000x40 px, RGBA) fuer eine Story.
Aufruf: python3 barometer_png.py   (verarbeitet alle Stories aus final_social_candidates.json)
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

_SPEKTREN = ["Links", "Mitte-Links", "Mitte", "Mitte-Rechts", "Rechts"]
_FARBEN = {
    "Links":        (0x4A, 0x7C, 0x59),
    "Mitte-Links":  (0x7B, 0xAE, 0x7F),
    "Mitte":        (0xC8, 0xA9, 0x6E),
    "Mitte-Rechts": (0xE8, 0xA8, 0x7C),
    "Rechts":       (0xC4, 0x61, 0x4A),
}
_ALPHA_VOLL  = 255
_ALPHA_LEER  = round(255 * 0.10)
_MIN_GEWICHT = 1  # Mindestgewicht damit 0-count Segmente sichtbar bleiben

BREITE = 1000
HOEHE  = 40


def barometer_erstellen(story: dict) -> Path:
    dist       = story.get("spectrum_distribution") or {}
    cluster_id = story.get("cluster_id", "unknown")

    gewichte = {s: max(dist.get(s, 0), _MIN_GEWICHT) for s in _SPEKTREN}
    gesamt   = sum(gewichte.values())

    img  = Image.new("RGBA", (BREITE, HOEHE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    x = 0
    for i, spektrum in enumerate(_SPEKTREN):
        anteil = gewichte[spektrum] / gesamt
        breite = BREITE - x if i == len(_SPEKTREN) - 1 else round(BREITE * anteil)

        alpha   = _ALPHA_LEER if dist.get(spektrum, 0) == 0 else _ALPHA_VOLL
        r, g, b = _FARBEN[spektrum]
        draw.rectangle([x, 0, x + breite - 1, HOEHE - 1], fill=(r, g, b, alpha))
        x += breite

    pfad = OUTPUT_DIR / f"barometer_{cluster_id}.png"
    img.save(pfad, "PNG")
    return pfad


if __name__ == "__main__":
    import json
    kandidaten_pfad = OUTPUT_DIR / "final_social_candidates.json"
    with open(kandidaten_pfad) as f:
        stories = json.load(f)
    for story in stories:
        pfad = barometer_erstellen(story)
        print(f"  ✓ {pfad.name}")
