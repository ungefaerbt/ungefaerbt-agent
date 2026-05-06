from collections import defaultdict

from cluster import _artikel_staerke


def ist_zu_vage(headline):
    if not headline or not headline.strip():
        return True
    woerter = headline.split()
    if len(woerter) < 5:
        return True
    stripped = headline.strip()
    if (stripped[0] in ('„', '"', '"', "'") and
            stripped[-1] in ('"', '"', '"', "'") and
            len(woerter) < 8):
        return True
    return False


def pro_quelle_filtern(artikel_liste, max_immer=3, dominanz_schwelle=0.25):
    """Weiche Quellen-Begrenzung:
    - Breaking News: unbegrenzt
    - Normale Artikel: bis 3 pro Quelle immer erlaubt
    - Mehr als 3 nur entfernen wenn Quelle die Ausgabe dominiert (> 25 %)
    - Bei Kürzung: schwächste Artikel zuerst entfernen
    """
    breaking = [a for a in artikel_liste if a.get("is_breaking", False)]
    normal = [a for a in artikel_liste if not a.get("is_breaking", False)]

    nach_quelle = defaultdict(list)
    for a in normal:
        nach_quelle[a["source"]].append(a)

    for src in nach_quelle:
        nach_quelle[src].sort(key=_artikel_staerke, reverse=True)

    gesamt_normal = sum(len(arts) for arts in nach_quelle.values())

    gefiltert = []
    for src, arts in nach_quelle.items():
        if len(arts) <= max_immer:
            gefiltert.extend(arts)
        else:
            anteil = len(arts) / gesamt_normal if gesamt_normal else 0
            if anteil > dominanz_schwelle:
                gefiltert.extend(arts[:max_immer])
            else:
                gefiltert.extend(arts)

    return breaking + gefiltert
