"""
clustering.py
-------------
Semantisches Clustering von Nachrichtenartikeln.

Verwendet Sentence-Embeddings statt Keyword-Matching, damit inhaltlich
gleiche Artikel geclustert werden - unabhaengig von der verwendeten Sprache
oder den konkreten Keywords.

Pipeline:
    1. Text aus headline + summary zusammenbauen
    2. Embeddings via Anthropic Voyage API (voyage-multilingual-2)
       Fallback: TF-IDF + SVD wenn API nicht verfügbar
    3. Dimensionsreduktion via PCA
    4. Clustering via HDBSCAN
    5. Datum-Filter: Artikel die zu weit auseinanderliegen nicht zusammenklappen
    6. Ausreisser nachtraeglich zuweisen via Cosine-Similarity
    7. cluster_id + cluster_size in jeden Artikel schreiben

Abhaengigkeiten:
    pip install anthropic scikit-learn numpy
"""

import hashlib
import logging
import os
import time
from collections import Counter
from datetime import datetime

import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA

logger = logging.getLogger("cluster")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)
logger.propagate = False


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

VOYAGE_MODEL    = "voyage-multilingual-2"
VOYAGE_RPM      = 20          # max Requests pro Minute
PCA_N_COMPONENTS = 5
MAX_TAGE_ABSTAND = 3
HDBSCAN_MIN_CLUSTER_SIZE = 2
HDBSCAN_MIN_SAMPLES = 1
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "voyage")
SENTENCE_TRANSFORMER_MODEL = os.getenv(
    "SENTENCE_TRANSFORMER_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2"
)
FASTEMBED_MODEL = os.getenv(
    "FASTEMBED_MODEL",
    "intfloat/multilingual-e5-small"
)
SIMILARITY_THRESHOLD = float(os.getenv(
    "SIMILARITY_THRESHOLD",
    "0.80" if EMBEDDING_BACKEND in ("sentence_transformers", "fastembed") else "0.65"
))


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

_sentence_model_cache = None
_fastembed_model_cache = None


def get_sentence_model():
    global _sentence_model_cache
    if _sentence_model_cache is not None:
        return _sentence_model_cache
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "sentence-transformers ist nicht installiert. "
            "Bitte 'pip install sentence-transformers' ausführen oder "
            "EMBEDDING_BACKEND=voyage setzen."
        ) from e
    logger.info("SentenceTransformer-Modell: %s", SENTENCE_TRANSFORMER_MODEL)
    _sentence_model_cache = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
    return _sentence_model_cache


def get_fastembed_model():
    global _fastembed_model_cache
    if _fastembed_model_cache is not None:
        return _fastembed_model_cache
    try:
        from fastembed import TextEmbedding
    except ImportError as e:
        raise ImportError(
            "fastembed ist nicht installiert. "
            "Bitte 'pip install fastembed' ausführen oder "
            "EMBEDDING_BACKEND=voyage setzen."
        ) from e
    logger.info("FastEmbed-Modell: %s", FASTEMBED_MODEL)
    _fastembed_model_cache = TextEmbedding(FASTEMBED_MODEL)
    return _fastembed_model_cache


def _fastembed_embeddings(texte):
    model = get_fastembed_model()
    arr = np.array(list(model.embed(texte)), dtype=np.float32)
    normen = np.linalg.norm(arr, axis=1, keepdims=True)
    normen = np.where(normen == 0, 1, normen)
    return arr / normen


def _artikel_zu_text(artikel):
    headline = artikel.get("headline", "")
    summary  = artikel.get("summary", "")
    teile = [headline, headline, summary]
    return " ".join(t for t in teile if t).strip()


# ---------------------------------------------------------------------------
# Embeddings — Voyage API mit TF-IDF Fallback
# ---------------------------------------------------------------------------

def _voyage_embeddings(texte):
    """
    Erzeugt Embeddings via Anthropic Voyage API.
    Gibt (embeddings_array, True) zurueck oder wirft eine Exception.
    Rate-Limit: VOYAGE_RPM Requests pro Minute via sleep.
    """
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client  = anthropic.Anthropic(api_key=api_key)

    alle = []
    delay = 60.0 / VOYAGE_RPM  # Sekunden zwischen Requests

    for i, text in enumerate(texte):
        response = client.embeddings.create(
            model=VOYAGE_MODEL,
            input=[text],
        )
        alle.append(response.embeddings[0].embedding)
        if i < len(texte) - 1:
            time.sleep(delay)

    arr = np.array(alle, dtype=np.float32)
    # L2-Normalisierung
    normen = np.linalg.norm(arr, axis=1, keepdims=True)
    normen = np.where(normen == 0, 1, normen)
    return arr / normen


def _tfidf_embeddings(texte):
    """
    TF-IDF + TruncatedSVD Fallback wenn Voyage nicht verfuegbar.
    Produziert 64-dimensionale normalisierte Vektoren.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import normalize

    n_components = min(64, len(texte) - 1) if len(texte) > 1 else 1
    vec = TfidfVectorizer(max_features=5000, sublinear_tf=True)
    X   = vec.fit_transform(texte)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    reduced = svd.fit_transform(X)
    return normalize(reduced).astype(np.float32)


def _embeddings_erstellen(texte):
    """
    Erzeugt Embeddings je nach EMBEDDING_BACKEND.
    "fastembed": ONNX-basiert, kein torch, kein API-Key (Railway Free Tier)
    "sentence_transformers": lokales PyTorch-Modell (gecacht, kein API-Key nötig)
    "voyage" (default): Voyage API mit TF-IDF Fallback
    """
    logger.info("Embedding-Backend: %s", EMBEDDING_BACKEND)

    if EMBEDDING_BACKEND == "fastembed":
        embeddings = _fastembed_embeddings(texte)
        logger.info("FastEmbed: %s Texte eingebettet.", len(texte))
        return embeddings

    if EMBEDDING_BACKEND == "sentence_transformers":
        model = get_sentence_model()
        arr = model.encode(texte, normalize_embeddings=True, convert_to_numpy=True)
        logger.info("SentenceTransformer: %s Texte eingebettet.", len(texte))
        return arr.astype(np.float32)

    try:
        embeddings = _voyage_embeddings(texte)
        logger.info("Voyage Embeddings: %s Texte via %s eingebettet.", len(texte), VOYAGE_MODEL)
        return embeddings
    except Exception as e:
        logger.warning("Voyage fehlgeschlagen (%s) — TF-IDF Fallback wird genutzt.", e)
        embeddings = _tfidf_embeddings(texte)
        logger.info("TF-IDF Fallback: %s Texte eingebettet.", len(texte))
        return embeddings


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
    # 2. Embeddings generieren (Voyage API, Fallback TF-IDF)
    # ------------------------------------------------------------------
    embeddings = _embeddings_erstellen(texte)

    # ------------------------------------------------------------------
    # 3. Dimensionsreduktion via PCA
    # ------------------------------------------------------------------
    if n > 2:
        n_components = min(PCA_N_COMPONENTS, n - 1)
        pca = PCA(n_components=n_components, random_state=42)
        reduced = pca.fit_transform(embeddings)
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
