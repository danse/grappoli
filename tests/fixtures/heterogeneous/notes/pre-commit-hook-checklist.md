Hooks run before the commit lands, which makes them the last place to
catch an accident. The checklist that pays for itself: a formatter, a
linter, a scan for secrets and keys, and a test suite kept deliberately
slow so the quick hooks stay quick.

A hook that blocks on style arguments gets deleted by whoever is in a
hurry, so keep the rules mechanical and the messages legible. One setup
script per machine keeps the whole team sharing the same behaviour.