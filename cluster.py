"""
clustering.py
-------------
Semantisches Clustering von Nachrichtenartikeln.

Verwendet Sentence-Embeddings statt Keyword-Matching, damit inhaltlich
gleiche Artikel geclustert werden - unabhaengig von der verwendeten Sprache
oder den konkreten Keywords.

Pipeline:
    1. Text aus headline + summary + kategorie zusammenbauen
    2. Embeddings via sentence-transformers generieren
    3. Dimensionsreduktion via UMAP
    4. Clustering via HDBSCAN
    5. Datum-Filter: Artikel die zu weit auseinanderliegen nicht zusammenklappen
    6. Ausreisser nachtraeglich zuweisen via Cosine-Similarity
    7. cluster_id + cluster_size in jeden Artikel schreiben

Abhaengigkeiten:
    pip install sentence-transformers umap-learn scikit-learn numpy
"""

import hashlib
from collections import Counter
from datetime import datetime

import numpy as np
from sklearn.cluster import HDBSCAN
from sentence_transformers import SentenceTransformer
from umap import UMAP


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"
MAX_TAGE_ABSTAND = 3
UMAP_N_COMPONENTS = 5
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.0
HDBSCAN_MIN_CLUSTER_SIZE = 2
HDBSCAN_MIN_SAMPLES = 1
SIMILARITY_THRESHOLD = 0.82


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _artikel_zu_text(artikel):
    """
    Baut einen Eingabe-String fuer das Embedding-Modell.
    Headline wird doppelt gewichtet da sie das Thema am praezisesten beschreibt.
    """
    headline = artikel.get("headline", "")
    summary = artikel.get("summary", "")
    kategorie = artikel.get("kategorie", "") or artikel.get("tag", "")

    teile = [headline, headline, summary, kategorie]
    return " ".join(t for t in teile if t).strip()


def _datum_parsen(artikel):
    """
    Liest das Datum aus dem Artikel.
    Gibt None zurueck wenn kein Datum vorhanden oder nicht parsebar.
    Erwartet ISO-Format z.B. 2024-05-07 oder 2024-05-07T14:30:00
    """
    raw = (
        artikel.get("datum")
        or artikel.get("date")
        or artikel.get("published_at")
    )
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw)[:10])
    except (ValueError, TypeError):
        return None


def _datum_zu_weit(a, b):
    """
    Gibt True zurueck wenn zwei Artikel zeitlich zu weit auseinanderliegen.
    """
    datum_a = _datum_parsen(a)
    datum_b = _datum_parsen(b)
    if datum_a is None or datum_b is None:
        return False
    return abs((datum_a - datum_b).days) > MAX_TAGE_ABSTAND


def _cosine_matrix(embeddings):
    """
    Berechnet die vollstaendige Cosine-Similarity-Matrix.
    Setzt voraus dass embeddings bereits L2-normalisiert sind.
    """
    return embeddings @ embeddings.T


# ---------------------------------------------------------------------------
# Union-Find
# ---------------------------------------------------------------------------

def _make_union_find(n):
    eltern = list(range(n))

    def find(x):
        while eltern[x] != x:
            eltern[x] = eltern[eltern[x]]
            x = eltern[x]
        return x

    def union(x, y):
        eltern[find(x)] = find(y)

    return eltern, find, union


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------

def _fingerprint_merge_pass(artikel_liste, embeddings_map):
    cluster_zu_idx = {}
    for i, a in enumerate(artikel_liste):
        cluster_zu_idx.setdefault(a["cluster_id"], []).append(i)

    grosse = {cid: idxs for cid, idxs in cluster_zu_idx.items() if len(idxs) >= 2}
    if len(grosse) < 2:
        return

    cluster_ids = list(grosse.keys())
    repraesentant = {
        cid: max(idxs, key=lambda i: artikel_liste[i].get("relevance_score", 0))
        for cid, idxs in grosse.items()
    }

    _, find_c, union_c = _make_union_find(len(cluster_ids))
    cid_pos = {cid: pos for pos, cid in enumerate(cluster_ids)}

    for i_pos, cid_i in enumerate(cluster_ids):
        for j_pos in range(i_pos + 1, len(cluster_ids)):
            cid_j = cluster_ids[j_pos]
            ri = repraesentant[cid_i]
            rj = repraesentant[cid_j]
            art_i = artikel_liste[ri]
            art_j = artikel_liste[rj]

            if _datum_zu_weit(art_i, art_j):
                continue

            emb_i = embeddings_map[ri]
            emb_j = embeddings_map[rj]
            sem_sim = float(np.dot(emb_i, emb_j))

            who_i = {w.lower() for w in (art_i.get("event_who") or [])}
            who_j = {w.lower() for w in (art_j.get("event_who") or [])}
            who_union = who_i | who_j
            who_sim = len(who_i & who_j) / len(who_union) if who_union else 0.0

            where_i = (art_i.get("event_where") or "").lower().strip()
            where_j = (art_j.get("event_where") or "").lower().strip()
            where_sim = 1.0 if where_i and where_j and where_i == where_j else 0.0

            what_i = set((art_i.get("event_what") or "").lower().split())
            what_j = set((art_j.get("event_what") or "").lower().split())
            what_union = what_i | what_j
            what_sim = len(what_i & what_j) / len(what_union) if what_union else 0.0

            aehnlichkeit = (
                0.45 * sem_sim
                + 0.25 * who_sim
                + 0.15 * where_sim
                + 0.15 * what_sim
            )

            if aehnlichkeit >= 0.75:
                union_c(cid_pos[cid_i], cid_pos[cid_j])

    neue_cid = {
        cid: cluster_ids[find_c(pos)]
        for pos, cid in enumerate(cluster_ids)
    }

    for artikel in artikel_liste:
        old = artikel["cluster_id"]
        if old in neue_cid:
            artikel["cluster_id"] = neue_cid[old]

    neue_groessen = Counter(a["cluster_id"] for a in artikel_liste)
    for artikel in artikel_liste:
        artikel["cluster_size"] = neue_groessen[artikel["cluster_id"]]


def artikel_clustern(artikel_liste, embeddings_map=None):
    """
    Clustert eine Liste von Artikeln semantisch.

    Jeder Artikel bekommt folgende Felder hinzugefuegt:
        - cluster_id   (int) gemeinsame ID pro Cluster
        - cluster_size (int) Anzahl Artikel in diesem Cluster

    Args:
        artikel_liste: Liste von Artikel-Dicts mit mindestens 'headline'

    Returns:
        Dieselbe Liste, angereichert mit cluster_id und cluster_size.
    """
    if not artikel_liste:
        return artikel_liste

    n = len(artikel_liste)

    # ------------------------------------------------------------------
    # 1. Texte aufbauen
    # ------------------------------------------------------------------
    texte = [_artikel_zu_text(a) for a in artikel_liste]

    # ------------------------------------------------------------------
    # 2. Embeddings generieren
    # ------------------------------------------------------------------
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(
        texte,
        show_progress_bar=True,
        batch_size=64,
        normalize_embeddings=True,
    )
    embeddings = np.array(embeddings)

    # ------------------------------------------------------------------
    # 3. Dimensionsreduktion via UMAP
    # ------------------------------------------------------------------
    if n > 2:
        n_components = min(UMAP_N_COMPONENTS, n - 1)
        n_neighbors = min(UMAP_N_NEIGHBORS, n - 1)

        umap_model = UMAP(
            n_components=n_components,
            n_neighbors=n_neighbors,
            min_dist=UMAP_MIN_DIST,
            metric="cosine",
            random_state=42,
        )
        reduced = umap_model.fit_transform(embeddings)
    else:
        reduced = embeddings

    # ------------------------------------------------------------------
    # 4. HDBSCAN Clustering
    # ------------------------------------------------------------------
    min_cluster_size = min(HDBSCAN_MIN_CLUSTER_SIZE, n)

    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(reduced)

    # ------------------------------------------------------------------
    # 5. HDBSCAN-Ergebnis in Union-Find ueberfuehren
    # ------------------------------------------------------------------
    eltern, find, union = _make_union_find(n)

    label_zu_indices = {}
    for i, label in enumerate(labels):
        if label == -1:
            continue
        label_zu_indices.setdefault(label, []).append(i)

    for indices in label_zu_indices.values():
        for k in indices[1:]:
            union(indices[0], k)

    # ------------------------------------------------------------------
    # 6. Datum-Filter: Cluster aufbrechen wenn Artikel zu weit auseinander
    # ------------------------------------------------------------------
    for indices in label_zu_indices.values():
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                idx_i = indices[i]
                idx_j = indices[j]
                if find(idx_i) == find(idx_j):
                    if _datum_zu_weit(artikel_liste[idx_i], artikel_liste[idx_j]):
                        eltern[find(idx_i)] = idx_i

    # ------------------------------------------------------------------
    # 7. Ausreisser nachtraeglich zuweisen via Cosine-Similarity
    # ------------------------------------------------------------------
    similarity_matrix = _cosine_matrix(embeddings)

    ausreisser = [i for i, label in enumerate(labels) if label == -1]
    for i in ausreisser:
        beste_sim = -1
        bester_j = -1
        for j in range(n):
            if j == i or labels[j] == -1:
                continue
            sim = float(similarity_matrix[i, j])
            if sim > beste_sim:
                beste_sim = sim
                bester_j = j
        if bester_j != -1 and beste_sim >= SIMILARITY_THRESHOLD:
            if not _datum_zu_weit(artikel_liste[i], artikel_liste[bester_j]):
                union(i, bester_j)

    # ------------------------------------------------------------------
    # 8. cluster_id und cluster_size schreiben
    # ------------------------------------------------------------------
    wurzeln = [find(i) for i in range(n)]
    groessen = Counter(wurzeln)

    for i, artikel in enumerate(artikel_liste):
        artikel["cluster_id"] = wurzeln[i]
        artikel["cluster_size"] = groessen[wurzeln[i]]

    # ------------------------------------------------------------------
    # 9. Fingerprint-Merge-Pass
    # ------------------------------------------------------------------
    if embeddings_map is None:
        embeddings_map = {i: embeddings[i] for i in range(n)}
    _fingerprint_merge_pass(artikel_liste, embeddings_map)

    return artikel_liste


def schlagzeilen_clustern(artikel_liste):
    return artikel_clustern(artikel_liste)


def _artikel_staerke(artikel):
    return (
        artikel.get("relevance_score", 0),
        artikel.get("cluster_size", 1),
        1 if artikel.get("is_top_story") else 0,
    )


def _cluster_fingerprint(artikel_liste):
    headlines = sorted(a.get("headline", "") for a in artikel_liste)
    combined = "|".join(headlines)
    return hashlib.md5(combined.encode("utf-8")).hexdigest()
