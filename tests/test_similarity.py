"""The control provider reads a corpus in any language.

TF-IDF is the bag-of-words baseline the encoder must beat on structure
match. It is a control, so it has to be held to the same rule as the
encoder: two notes that differ only in the function words of the
language they are written in are about the same thing, whatever that
language is. An English stopword list and an English tokeniser could not
say so about a branch in any other language (`words.py`).
"""

from pathlib import Path

import numpy as np
import pytest

from grappoli.corpus import load_corpus
from grappoli.similarity import tfidf_vectors
from grappoli.words import stopwords

FIXTURES = Path(__file__).parent / "fixtures"
ENGLISH_CORPORA = [
    pytest.param(FIXTURES / "in-domain" / "notes", id="in-domain"),
    pytest.param(FIXTURES / "heterogeneous" / "notes", id="heterogeneous"),
]
MULTILINGUAL = FIXTURES / "multilingual" / "notes"


def _cosine(left, right):
    return float(left @ right)


def test_tfidf_drops_another_languages_function_words():
    """`della` and `che` are Italian's, not English's, so the English list
    the control used to carry kept them as terms and scored apart two
    notes that say the same thing."""
    vectors = tfidf_vectors(["il gatto della casa", "il gatto che casa"])
    assert np.isclose(_cosine(vectors[0], vectors[1]), 1.0)


def test_tfidf_will_not_keep_a_two_letter_function_word():
    """The term floor is three letters in any language, and the stopword
    set is filtered to it, so the tokeniser has to be too — otherwise
    `of` and `la` survive as terms the set was told to drop."""
    vectors = tfidf_vectors(["of the compiler reads", "the compiler reads"])
    assert np.isclose(_cosine(vectors[0], vectors[1]), 1.0)


@pytest.mark.parametrize("notes_dir", ENGLISH_CORPORA)
def test_the_english_fixtures_are_read_as_english(notes_dir):
    """The control's recorded numbers are the English sweep, so the
    English fixtures have to keep being found English: a corpus the lists
    could not place would keep every function word and move the control
    with no record of it."""
    corpus = load_corpus(notes_dir)
    assert {"the", "and"} <= stopwords(corpus.values())


def test_the_multilingual_fixture_is_read_as_both_languages():
    """The mixed fixture is Italian as much as English, so the control
    must drop both languages' function words. Reading it as one language
    would keep the other's grammar in as evidence, held by language
    rather than by subject (`tests/test_words.py` pins the detection)."""
    corpus = load_corpus(MULTILINGUAL)
    found = stopwords(corpus.values())
    assert {"the", "and"} <= found, "the English half"
    assert {"che", "della"} <= found, "the Italian half"
