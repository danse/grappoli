"""Note similarity. Two providers:

* `bge` — vectors from BAAI/bge-small-en-v1.5 (architecture.md).
* `tfidf` — bag-of-words cosine, the control the encoder must beat on
  structure match or it is not earning its place.

Both return L2-normalised row vectors, so cosine between rows is a dot
product and the graph step is uniform across providers.

Encoding is batched and reports progress through the `progress`
callback — a note at a time at Stage 1 cost.
"""

import numpy as np

MODEL_NAME = "BAAI/bge-small-en-v1.5"

_BGE_MODEL = None


def tfidf_vectors(notes: list[str]) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer

    matrix = TfidfVectorizer(strip_accents="unicode", stop_words="english").fit_transform(notes)
    return _normalise(matrix.toarray().astype(np.float32))


def bge_vectors(notes: list[str], progress=None) -> np.ndarray:
    global _BGE_MODEL
    if _BGE_MODEL is None:
        from sentence_transformers import SentenceTransformer

        _BGE_MODEL = SentenceTransformer(MODEL_NAME)

    batch = 4
    chunks = []
    for start in range(0, len(notes), batch):
        part = notes[start : start + batch]
        chunks.append(np.asarray(_BGE_MODEL.encode(part, normalize_embeddings=True), dtype=np.float32))
        if progress is not None:
            progress("embed", min(start + batch, len(notes)), len(notes))
    return _normalise(np.concatenate(chunks))


def build_vectors(notes: list[str], provider: str, progress=None) -> np.ndarray:
    if provider == "bge":
        return bge_vectors(notes, progress)
    if provider == "tfidf":
        return tfidf_vectors(notes)
    raise ValueError(f"unknown similarity provider: {provider!r}")


def _normalise(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms > 0)