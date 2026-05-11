"""
Smoke Test: cluster.schlagzeilen_clustern

Szenarien
---------
Memmingen (3 Artikel): Artikel 0+1 via Stufe 1, Artikel 2 via Stufe 3 → alle im gleichen Cluster
Leipzig   (2 Artikel): Artikel 3+4 via Stufe 2 (nur 1 gemeinsames Headline-Keyword, aber
                        Anchor-Check greift korrekt) → im gleichen Cluster
Merz      (2 Artikel): Artikel 5+6 via Stufe 1 → im gleichen Cluster
Trennung              : Memmingen ≠ Leipzig – der Anchor-Check verhindert Merge trotz
                        5 gemeinsamer Kombi-Keywords (Kriminalvokabular im Teaser)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from cluster import schlagzeilen_clustern


def art(headline, teaser):
    return {"headline": headline, "teaser": teaser, "political_leaning": "Mitte"}


ARTIKEL = [
    # ── Memmingen ────────────────────────────────────────────────────────────
    # Art 0 + 1: Stufe 1  (2 gemeinsame Headline-KW: "memmingen", "amokfahrt")
    art(
        "Memmingen: Amokfahrt erschüttert Stadt",
        "In Memmingen raste ein Täter in eine Menschenmenge. Polizei ist in Memmingen vor Ort.",
    ),
    art(
        "Amokfahrt Memmingen – Täter in Haft",
        "Nach der Amokfahrt in Memmingen sitzt der Täter in Haft. Memmingen trauert.",
    ),
    # Art 2: Singleton nach Stufe 1+2, dann Stufe 3 via Kernthema "memmingen"
    art(
        "Polizei sucht Zeugen in Memmingen",
        "Die Polizei Memmingen sucht nach Zeugen der Tat in Memmingen. "
        "Der Täter raste in eine Menschenmenge. Festnahme in Memmingen erfolgte.",
    ),
    # ── Leipzig ──────────────────────────────────────────────────────────────
    # Art 3 + 4: Stufe 2  (nur 1 gemeinsames Headline-KW "leipzig", aber Anchor-Check
    #                       erlaubt Merge weil "leipzig" in BEIDEN Headlines steht)
    # Wichtig: Art 2 (Memmingen) teilt mit Art 3 fünf Kombi-KW (polizei, zeugen, täter,
    #           raste, menschenmenge), aber KEIN Wort ist in BEIDEN Headlines → kein Merge
    art(
        "Leipzig: Tote nach Vorfall in Innenstadt",
        "In Leipzig raste ein Täter in eine Menschenmenge. "
        "Polizei nahm den Verdächtigen fest. Zeugen gesucht.",
    ),
    art(
        "Amokfahrt Leipzig – Motiv unklar",
        "Nach dem Vorfall in Leipzig ermittelt die Polizei wegen Amokfahrt. Tote zu beklagen.",
    ),
    # ── Merz ─────────────────────────────────────────────────────────────────
    # Art 5 + 6: Stufe 1  (3 gemeinsame Headline-KW: "merz", "vertrauensfrage", "bundestag")
    art(
        "Merz stellt Vertrauensfrage im Bundestag",
        "Bundeskanzler Friedrich Merz stellte die Vertrauensfrage im Bundestag. "
        "SPD und Grüne wollen zustimmen.",
    ),
    art(
        "Bundestag: Merz gewinnt Vertrauensfrage",
        "Friedrich Merz hat die Vertrauensfrage im Bundestag gewonnen. Koalition bleibt stabil.",
    ),
]


def _ids(ergebnis, indices):
    return [ergebnis[i]["cluster_id"] for i in indices]


def test_szenarien():
    ergebnis = schlagzeilen_clustern(ARTIKEL)

    mem_ids  = _ids(ergebnis, [0, 1, 2])
    lei_ids  = _ids(ergebnis, [3, 4])
    merz_ids = _ids(ergebnis, [5, 6])

    checks = [
        (
            len(set(mem_ids)) == 1,
            "Memmingen (3 Artikel) korrekt geclustert",
            f"Memmingen-Artikel getrennt: cluster_ids={mem_ids}",
        ),
        (
            len(set(lei_ids)) == 1,
            "Leipzig (2 Artikel) korrekt geclustert",
            f"Leipzig-Artikel getrennt: cluster_ids={lei_ids}",
        ),
        (
            len(set(merz_ids)) == 1,
            "Merz (2 Artikel) korrekt geclustert",
            f"Merz-Artikel getrennt: cluster_ids={merz_ids}",
        ),
        (
            not (set(mem_ids) & set(lei_ids)),
            "Anchor-Check: Memmingen != Leipzig (getrennt)",
            f"Anchor-Check FEHLER – fälschlich zusammengeführt! "
            f"memmingen={mem_ids}, leipzig={lei_ids}",
        ),
        (
            not (set(merz_ids) & (set(mem_ids) | set(lei_ids))),
            "Merz getrennt von Memmingen und Leipzig",
            f"Merz fälschlich mit anderem Cluster zusammengeführt! merz={merz_ids}",
        ),
    ]

    failed = False
    for ok, label, fehler in checks:
        if ok:
            print(f"  OK   {label}")
        else:
            print(f"  FAIL FEHLER: {fehler}")
            failed = True

    if failed:
        print("\n[FAILED]")
        sys.exit(1)
    else:
        print("\n[PASSED] Alle Tests bestanden.")


if __name__ == "__main__":
    print("\n=== Cluster Smoke Test ===\n")
    test_szenarien()
