from collections import defaultdict

from config import KATEGORIE_REIHENFOLGE


def feed_sortieren(artikel_liste):
    """Abwechslungsreiche Sortierung:
    - Breaking News ganz oben
    - Dann Kategorien im Wechsel (KATEGORIE_REIHENFOLGE)
    - Innerhalb jeder Kategorie: höchster relevance_score zuerst
    - is_top_story Artikel gleichmäßig über den Feed verteilt
    """
    breaking = [a for a in artikel_liste if a.get("is_breaking", False)]
    normal = [a for a in artikel_liste if not a.get("is_breaking", False)]

    nach_kategorie = defaultdict(list)
    for a in normal:
        nach_kategorie[a.get("category", "Sonstiges")].append(a)

    for kat in nach_kategorie:
        nach_kategorie[kat].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    cats = [k for k in KATEGORIE_REIHENFOLGE if k in nach_kategorie]
    cats += [k for k in nach_kategorie if k not in KATEGORIE_REIHENFOLGE]

    reihe = []
    while any(nach_kategorie[k] for k in cats):
        for kat in cats:
            if nach_kategorie[kat]:
                reihe.append(nach_kategorie[kat].pop(0))

    top_stories = [a for a in reihe if a.get("is_top_story", False)]
    non_top = [a for a in reihe if not a.get("is_top_story", False)]

    if not top_stories:
        return breaking + reihe

    gesamt = len(reihe)
    schritt = gesamt / len(top_stories)
    ergebnis = []
    top_idx = 0
    non_top_idx = 0

    for i in range(gesamt):
        if top_idx < len(top_stories) and i >= round(top_idx * schritt):
            ergebnis.append(top_stories[top_idx])
            top_idx += 1
        elif non_top_idx < len(non_top):
            ergebnis.append(non_top[non_top_idx])
            non_top_idx += 1

    ergebnis.extend(top_stories[top_idx:])
    ergebnis.extend(non_top[non_top_idx:])

    return breaking + ergebnis
