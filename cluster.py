from collections import Counter, defaultdict

from config import ALLE_AUSRICHTUNGEN, _STOPPWOERTER


def _artikel_staerke(a):
    return (
        a.get("relevance_score", 0),
        1 if a.get("image_url") else 0,
        len(a.get("summary", "")),
    )


def _cluster_fingerprint(artikel_list):
    sonderzeichen = '„""»«\'"\\-.,!?:()'
    alle_woerter = []
    for a in artikel_list:
        alle_woerter.extend([
            w.strip(sonderzeichen).lower()
            for w in a["headline"].split()
            if len(w.strip(sonderzeichen)) > 3
            and w.strip(sonderzeichen).lower() not in _STOPPWOERTER
        ])
    counter = Counter(alle_woerter)
    top_woerter = sorted(w for w, _ in counter.most_common(5))
    return "|".join(top_woerter)


def schlagzeilen_clustern(artikel_liste):
    sonderzeichen = '„""»«\'"\\-.,!?:()'

    def keywords(text):
        return {
            w.strip(sonderzeichen).lower()
            for w in text.split()
            if len(w.strip(sonderzeichen)) > 3
            and w.strip(sonderzeichen).lower() not in _STOPPWOERTER
        }

    n = len(artikel_liste)
    eltern = list(range(n))

    def find(x):
        while eltern[x] != x:
            eltern[x] = eltern[eltern[x]]
            x = eltern[x]
        return x

    # Stufe 1: 2+ gemeinsame Keywords aus Headline
    kw_headline = [keywords(a["headline"]) for a in artikel_liste]
    for i in range(n):
        for j in range(i + 1, n):
            if len(kw_headline[i] & kw_headline[j]) >= 2:
                eltern[find(i)] = find(j)

    # Singletons nach Stufe 1 ermitteln
    wurzeln_s1 = [find(i) for i in range(n)]
    groessen_s1 = Counter(wurzeln_s1)
    singletons = [i for i in range(n) if groessen_s1[wurzeln_s1[i]] == 1]

    # Stufe 2: Headline + Teaser kombiniert, 3+ Keywords, nur für Singletons
    kw_kombi = [
        keywords(a["headline"] + " " + a.get("teaser", ""))
        for a in artikel_liste
    ]
    for idx_i in range(len(singletons)):
        i = singletons[idx_i]
        for idx_j in range(idx_i + 1, len(singletons)):
            j = singletons[idx_j]
            if find(i) != find(j) and len(kw_kombi[i] & kw_kombi[j]) >= 3:
                eltern[find(i)] = find(j)

    # Singletons nach Stufe 2 ermitteln
    wurzeln_s2 = [find(i) for i in range(n)]
    groessen_s2 = Counter(wurzeln_s2)
    singletons_s2 = [i for i in range(n) if groessen_s2[wurzeln_s2[i]] == 1]

    # Stufe 4: Kernthema – häufigstes Named Entity (Großbuchstabe, ≥6 Zeichen) in Headline+Teaser
    # Bindestrich-Komposita werden gesplittet, jedes Teil nochmals gestrippt
    def kernthema(text):
        kandidaten = []
        for w in text.split():
            for teil in w.strip(sonderzeichen).split('-'):
                teil = teil.strip(sonderzeichen)
                if teil and teil[0].isupper() and len(teil) >= 6 and teil.lower() not in _STOPPWOERTER:
                    kandidaten.append(teil.lower())
        if not kandidaten:
            return None
        return Counter(kandidaten).most_common(1)[0][0]

    thema_zu_idx = defaultdict(list)
    for i in singletons_s2:
        kt = kernthema(
            artikel_liste[i]["headline"] + " " + artikel_liste[i].get("teaser", "")
        )
        if kt:
            thema_zu_idx[kt].append(i)

    for indices in thema_zu_idx.values():
        if len(indices) >= 2:
            for k in indices[1:]:
                ri, rk = find(indices[0]), find(k)
                if ri != rk:
                    eltern[rk] = ri

    wurzeln = [find(i) for i in range(n)]
    groessen = Counter(wurzeln)

    for i, artikel in enumerate(artikel_liste):
        artikel["cluster_id"] = wurzeln[i]
        artikel["cluster_size"] = groessen[wurzeln[i]]

    # Spectrum-Analyse pro Cluster
    cluster_gruppen = defaultdict(list)
    for a in artikel_liste:
        cluster_gruppen[a["cluster_id"]].append(a)

    for gruppe in cluster_gruppen.values():
        vorhandene = {a.get("political_leaning", "") for a in gruppe}
        stille = [s for s in ALLE_AUSRICHTUNGEN if s not in vorhandene]
        count = len(vorhandene & set(ALLE_AUSRICHTUNGEN))
        score = round(len(stille) / len(ALLE_AUSRICHTUNGEN) * 100)

        if len(gruppe) == 1:
            label = "Einzelmeldung"
        elif not stille:
            label = "Vollspektrum"
        elif set(stille) <= {"Rechts", "Mitte-Rechts"}:
            label = "Rechts-Blindspot"
        elif set(stille) <= {"Links", "Mitte-Links"}:
            label = "Links-Blindspot"
        elif stille == ["Mitte"]:
            label = "Mitte-Blindspot"
        else:
            label = "Gemischter Blindspot"

        for a in gruppe:
            a["spectrum_count"] = count
            a["silent_spectrums"] = stille
            a["blindspot_score"] = score
            a["blindspot_label"] = label

    return artikel_liste
