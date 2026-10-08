Rebasing rewrites the past, which is why it belongs on branches that
are yours alone. The working routine: pull the main branch, rebase your
work on top of it, resolve conflicts inside your own commits rather
than in a merge, and force-push only to a branch nobody else has
checked out.

Conflicts come one at a time through a rebase, and each is a small
decision taken calmly. The reflog is the undo button; keep it for a
week after a rewrite.