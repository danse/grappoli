# AGENTS.md

`product.md` is the spec. Read it before starting work on anything here —
it says what this project is for and why, which nothing else records.

There is no code yet, so for now it is the truth. Once code exists, where
the two disagree the code is what runs, so the code is what is true, and
the gap is worth closing rather than papering over. Cite a section when
one bears on the task; do not treat it as the arbiter of what the code
should be.

If a task needs a decision neither `product.md` nor the code settles,
say so rather than picking one quietly. Settle it then; do not leave it
flagged in the source for later, where it will be one of many and none
of them ordered.

The tests are the specification for behaviour: they are the record of
what was decided. Each names what it pins, and carries in its docstring
the reasoning behind it where there is some worth carrying — once, next
to the behaviour, not also in the source above it.

Verify behaviour by extending the tests, not with throwaway ones. A
scratch script under `/tmp`, a shell loop that edits the source to watch
a test fail, a one-off `python -c` that probes a function — none of these
are tests, and none of them survive. If a behaviour is worth checking,
it is worth a test in `tests/` that stays.

Don't worry about what's committed — users handle commits, agents don't.
