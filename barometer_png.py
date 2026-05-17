"""
barometer_png.py
----------------
Generiert ein Spektrum-Barometer-PNG (1080x60 px) fuer eine Story.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

WIDTH      = 1080
HEIGHT     = 60
BAR_HEIGHT = 28
LBL_HEIGHT = 32   # HEIGHT - BAR_HEIGHT

COLOR_BG    = (0x1C, 0x18, 0x14)
COLOR_EMPTY = (0x33, 0x33, 0x33)
COLOR_LABEL = (0xAA, 0xAA, 0xAA)
FONT_SIZE   = 11
MIN_WIDTH   = 20

_SPEKTREN = ["Links", "Mitte-Links", "Mitte", "Mitte-Rechts", "Rechts"]
_LABELS   = ["LINKS", "MITTE-L.", "MITTE", "MITTE-R.", "RECHTS"]
_FARBEN   = {
    "Links":        (0x4A, 0x7C, 0x59),
    "Mitte-Links":  (0x7B, 0xAE, 0x7F),
    "Mitte":        (0xC8, 0xA9, 0x6E),
    "Mitte-Rechts": (0xE8, 0xA8, 0x7C),
    "Rechts":       (0xC4, 0x61, 0x4A),
}

_FONT_CANDIDATES = [
    "/Library/Fonts/DMSans-Regular.ttf",
    "/Library/Fonts/DM Sans Regular.ttf",
    "/Library/Fonts/DM Sans.ttf",
    "/Library/Fonts/Inter-Regular.ttf",
    "/Library/Fonts/Inter Regular.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _segment_widths(dist: dict) -> list[int]:
    counts     = [dist.get(s, 0) for s in _SPEKTREN]
    total      = sum(counts)
    zero_count = sum(1 for c in counts if c == 0)
    reserved   = zero_count * MIN_WIDTH
    remaining  = WIDTH - reserved

    widths = []
    for c in counts:
        if c == 0:
            widths.append(MIN_WIDTH)
        else:
            widths.append(round(c / total * remaining) if total else 0)

    # Rounding-Korrektur: letztes nicht-leeres Segment füllt auf exakt WIDTH auf
    diff = WIDTH - sum(widths)
    if diff != 0:
        for idx in range(len(widths) - 1, -1, -1):
            if counts[idx] > 0:
                widths[idx] += diff
                break

    return widths


def generate_barometer(spectrum_distribution: dict, cluster_id) -> Path:
    dist   = spectrum_distribution or {}
    widths = _segment_widths(dist)
    font   = _load_font(FONT_SIZE)

    img  = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    x = 0
    for i, spektrum in enumerate(_SPEKTREN):
        w     = widths[i]
        color = COLOR_EMPTY if dist.get(spektrum, 0) == 0 else _FARBEN[spektrum]

        # Farb-Balken
        draw.rectangle([x, 0, x + w - 1, BAR_HEIGHT - 1], fill=color)

        # Label zentriert darunter
        label = _LABELS[i]
        bbox  = draw.textbbox((0, 0), label, font=font)
        lw    = bbox[2] - bbox[0]
        lx    = x + (w - lw) // 2
        ly    = BAR_HEIGHT + (LBL_HEIGHT - (bbox[3] - bbox[1])) // 2
        draw.text((lx, ly), label, fill=COLOR_LABEL, font=font)

        x += w

    pfad = OUTPUT_DIR / f"barometer_{cluster_id}.png"
    img.save(pfad, "PNG")
    return pfad


# ---------------------------------------------------------------------------
# Hilfsfunktion fuer email_report.py (liest spectrum_distribution aus story)
# ---------------------------------------------------------------------------

def barometer_erstellen(story: dict) -> Path:
    return generate_barometer(
        story.get("spectrum_distribution") or {},
        story.get("cluster_id", "unknown"),
    )


# ---------------------------------------------------------------------------
# Testlauf
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_dist = {
        "Links":        4,
        "Mitte-Links":  6,
        "Mitte":        5,
        "Mitte-Rechts": 3,
        "Rechts":       1,
    }
    pfad = generate_barometer(test_dist, "test")
    print(f"Gespeichert: {pfad}")

    # Auch mit 0-count Segmenten testen
    test_dist_zero = {
        "Links":        0,
        "Mitte-Links":  4,
        "Mitte":        0,
        "Mitte-Rechts": 3,
        "Rechts":       0,
    }
    pfad2 = generate_barometer(test_dist_zero, "test_zero")
    print(f"Gespeichert: {pfad2}")
