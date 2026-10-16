"""Which words carry meaning, and which a language says nothing with.

The terms the relation tools compare come from here. These pin the two
faults the language lists replaced: an English-only list that left
another language's function words in as evidence, and an ASCII tokeniser
that shortened an accented word instead of keeping it. They also pin the
detection that decides which lists apply — including the corpora it
declines to decide for, where stripping nothing is the honest answer.
"""

from grappoli.words import MIN_LENGTH, stopwords, terms, words


# A body of English, an Italian one, and one in both, each written with
# enough function words that its own list accounts for a good share of it.
ENGLISH = [
    "the compiler reads and writes a corpus of notes",
    "the compiler builds an index over the corpus",
    "an index reads the notes and writes a map",
]
ITALIAN = [
    "il centro della città della scuola che apre",
    "il mercato della città della scuola che chiude",
    "il giardino della città che fiorisce",
]
MIXED = [
    "il centro della città della scuola che apre",
    "il mercato della città della scuola che chiude",
    "the shed needs a new roof",
    "the compiler reads a corpus of notes",
]


def test_words_split_on_letters_in_any_script():
    """A word is letters and digits, not the twenty-six of ASCII.

    Under an ASCII pattern Cyrillic, Greek and Hebrew vanish entirely —
    no terms and no edges from a corpus in those scripts.
    """
    assert words("la città del giardino") == {"città", "del", "giardino"}
    assert words("привет мир") == {"привет", "мир"}
    assert words("γεια σου κόσμε") == {"γεια", "σου", "κόσμε"}


def test_a_word_of_one_or_two_letters_is_not_a_term():
    assert words("a of the graph, or graph.") == {"the", "graph"}


def test_a_word_is_a_set_not_a_count():
    """Repetition inside one text is not evidence the text is about it."""
    assert words("graph graph graph") == words("graph")


def test_two_words_differing_only_by_an_accent_are_two_terms():
    """Shortening a word is worse than dropping it: `citta` and `città`
    are different words, and a graph that cannot tell them apart joins
    two notes about different places."""
    assert words("citta città") == {"citta", "città"}


def test_terms_drop_only_the_words_they_are_given():
    assert terms("the compiler reads a corpus", frozenset({"the", "corpus"})) == {
        "compiler", "reads",
    }
    assert terms("the compiler reads a corpus") == {
        "the", "compiler", "reads", "corpus",
    }


def test_an_english_corpus_drops_its_function_words():
    found = stopwords(ENGLISH)
    assert {"the", "and"} <= found
    assert "compiler" not in found, "a contentful noun is not a stopword"
    assert terms("the compiler reads and writes", found) == {"compiler", "reads", "writes"}


def test_an_italian_corpus_drops_its_own_function_words():
    """`che` and `della` are distinctive to an English list because they
    are absent from it; the notes say what their language's function
    words are, so they are dropped."""
    found = stopwords(ITALIAN)
    assert {"che", "della"} <= found
    assert "centro" not in found and "giardino" not in found
    assert terms("il giardino fiorisce", found) == {"giardino", "fiorisce"}


def test_a_mixed_corpus_drops_both_languages_function_words():
    """Stopping at the language with the most notes would leave `della`
    in an Italian half of the branch as evidence, held by grammar rather
    than by subject."""
    found = stopwords(MIXED)
    assert {"della", "che"} <= found, "the Italian half"
    assert {"the"} <= found, "and the English half"
    assert "centro" not in found and "compiler" not in found


def test_a_corpus_of_nouns_keeps_every_word():
    """No list accounts for three notes about kettles, so no language is
    detected and nothing is dropped. Guessing English would strip a
    corpus nobody asked to have stripped."""
    corpus = ["a kettle boils", "a kettle cools", "a kettle stands"]
    assert stopwords(corpus) == frozenset()
    assert terms("a kettle boils", stopwords(corpus)) == {"kettle", "boils"}


def test_a_single_word_detects_no_language():
    """A word is not a language, and one note says nothing about one."""
    assert stopwords(["lamination"]) == frozenset()


def test_no_stopword_is_shorter_than_the_term_floor():
    """A stopword set that disagreed with `words()` on length would make
    `terms()` depend on which set it was handed."""
    found = stopwords(ENGLISH)
    assert found
    assert all(len(word) >= MIN_LENGTH for word in found)
