r"""Words, and the words a language says nothing with.

A term is a word that carries something. Which words carry nothing is a
fact about the language a note is written in — `the`, `della`, `der` —
so the lists come from `stopwordsiso` rather than a set kept here: a set
kept here can only answer for the language it was written in, which is
what made a corpus in any other language read as prose full of function
words (`architecture.md`, Language).

The language is not guessed. Each language's list is scored by how much
of the corpus it accounts for, and every language clearing half of the
best score counts as written. An English branch drops `the`, an Italian
one drops `della`, and a branch written in both drops both. A corpus
whose words no list accounts for — a branch of nouns, a single note —
detects no language and keeps every word, which is the honest answer
rather than a default that would strip a language nobody enumerated.

Two rules are language-independent on purpose. A word is cut on letters
and digits in any script (`[^\W_]+`): an ASCII pattern does not merely
lose a word it cannot read, it shortens the one it is in the middle of,
so "città" becomes "citt" and joins every other word beginning "citt".
And a word of one or two letters is no term in any language, so that
floor is about letters, not about language.
"""

import re
from collections.abc import Iterable
from functools import cache

from stopwordsiso import has_lang, langs
from stopwordsiso import stopwords as stopword_lists

# A word shorter than this carries no distinction, in any language.
MIN_LENGTH = 3

# A language counts as written when its list accounts for at least this
# fraction of the best one's. A ratio and not a share of the vocabulary,
# because the two are measured against different things: a fixed share
# would be a threshold on how much grammar a corpus has, and would drop a
# language written briefly in a corpus dominated by another. Half, and
# the gap is wide enough not to need care — an English corpus scores
# about a quarter against English and a twentieth against anything else.
DETECTION_RATIO = 2

# Letters and digits, in any script.
_WORD = re.compile(r"[^\W_]+")


def words(text: str) -> set[str]:
    """Every word in a text that could carry meaning, in any script.

    A set, not a count: how often a word repeats inside one text is not
    evidence that the text is about it.
    """
    return {word for word in _WORD.findall(text.lower()) if len(word) >= MIN_LENGTH}


def terms(text: str, stop: frozenset[str] = frozenset()) -> set[str]:
    """A text's distinctive terms: its words less the words it says nothing with.

    `stop` is the corpus's, passed in rather than looked up, so reading
    one text's terms needs no global state and two stages cannot disagree
    about which words those are by accident.
    """
    return words(text) - stop


@cache
def _lists() -> dict[str, frozenset[str]]:
    """Every language's stopwords, read once."""
    return {lang: frozenset(stopword_lists(lang)) for lang in langs() if has_lang(lang)}


def _detect(texts: Iterable[str]) -> frozenset[str]:
    """Which languages these texts are written in.

    Scored by how much of their vocabulary each language's list accounts
    for, which is the one measurement that says a language rather than
    guesses it: an English corpus covers about a quarter of its words
    with the English list and a twentieth with any other, so half of the
    best sits in a wide gap.

    A stopword list is the detector as well as the answer, so no second
    list has to keep in step with it. A keyword list would: `di` is
    Italian and also the French past participle of `dire`, and `die` is
    German and also an English verb, so it would have to disambiguate
    what the coverage already settles. Both halves of a mixed corpus are
    found, because the union of two languages is still best explained by
    each of them.
    """
    vocabulary = words(" ".join(texts))
    if not vocabulary:
        return frozenset()
    scores = {
        lang: len(vocabulary & every) / len(vocabulary)
        for lang, every in _lists().items()
    }
    best = max(scores.values())
    if not best:
        return frozenset()
    return frozenset(
        lang for lang, score in scores.items() if score >= best / DETECTION_RATIO
    )


def stopwords(texts: Iterable[str]) -> frozenset[str]:
    """The words these texts are written with and mean nothing by.

    The languages the corpus is written in are detected and their lists
    unioned, so an English branch drops `the` and an Italian one drops
    `della`, and a branch in both drops both.

    Length-filtered to `MIN_LENGTH` and shape-filtered to `words()`'s
    own terms, because a one or two letter word is no term and neither is
    one `words()` would split (`ain't` is `ain`). A stopword set that
    disagreed with `words()` would make `terms()` depend on which set it
    was given, and one holding a word the tokeniser never produces would
    warn where it is handed to a tokeniser of its own (similarity).
    """
    found: set[str] = set()
    for lang in _detect(texts):
        found |= _lists()[lang]
    return frozenset(
        word for word in found if word.isalnum() and len(word) >= MIN_LENGTH
    )
