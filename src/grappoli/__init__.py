"""grappoli — maps a branch of notes.

The command is `grappoli.cli` (`read`, `measure`, `show`); the pipeline
is `map` (arithmetic), `characterise` (one model call per region),
`relations` (one agent loop) and `render` (the page), with generation
behind the single interface in `model`. The
reason this is a package rather than a bare script is pyproject.toml's
CPU-only torch pin: uv honours `[tool.uv.sources]` only for a package
project.
"""
