"""Note similarity. Two providers:

* `e5` — vectors from intfloat/multilingual-e5-small (architecture.md).
* `tfidf` — bag-of-words cosine, the control the encoder must beat on
  structure match or it is not earning its place.

Both return L2-normalised row vectors, so cosine between rows is a dot
product and the graph step is uniform across providers.

Encoding is batched and reports progress through the `progress`
callback — a note at a time, at the cost the throughput record gives.
"""

import numpy as np

from .words import stopwords

# A multilingual encoder, so a branch in any of a hundred languages is
# embedded by the same model rather than only an English one. 384
# dimensions, small enough for CPU.
MODEL_NAME = "intfloat/multilingual-e5-small"

_MODEL = None


def tfidf_vectors(notes: list[str]) -> np.ndarray:
    """Bag-of-words cosine over the corpus's own terms.

    The stopwords are the corpus's, from `words.stopwords`, so the
    control reads a branch in any language by one rule; the English list
    it used to carry kept every function word of any other (`words.py`).

    The token pattern is the term floor `words()` uses — three letters or
    more, in any script — because the corpus's stopword set is filtered to
    it. sklearn's default would keep the two-letter function words of
    every language (`of`, `la`, `de`) that the floor calls no term, and a
    set that dropped them would not match the text as tokenised. Accents
    are left alone, so an accented stopword matches the word it should
    drop and `citta` and `città` stay two terms.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    matrix = TfidfVectorizer(
        token_pattern=r"(?u)\b\w\w\w+\b",
        stop_words=sorted(stopwords(notes)),
    ).fit_transform(notes)
    return _normalise(matrix.toarray().astype(np.float32))


def e5_vectors(notes: list[str], progress=None) -> np.ndarray:
    """Vectors from the multilingual encoder.

    The prefix is the model's own, not a prompt: e5 is trained with
    `query: ` and `passage: ` in front of its two sides, and a branch of
    notes is the passage side throughout, so every note carries it.
    """
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer(MODEL_NAME)

    texts = [f"passage: {note}" for note in notes]
    batch = 4
    chunks = []
    for start in range(0, len(texts), batch):
        part = texts[start : start + batch]
        chunks.append(np.asarray(_MODEL.encode(part, normalize_embeddings=True), dtype=np.float32))
        if progress is not None:
            progress("embed", min(start + batch, len(notes)), len(notes))
    return _normalise(np.concatenate(chunks))


def build_vectors(notes: list[str], provider: str, progress=None) -> np.ndarray:
    if provider == "e5":
        return e5_vectors(notes, progress)
    if provider == "tfidf":
        return tfidf_vectors(notes)
    raise ValueError(f"unknown similarity provider: {provider!r}")


def _normalise(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms > 0)
