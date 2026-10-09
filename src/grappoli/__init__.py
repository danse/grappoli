"""grappoli — maps a branch of notes.

The command is `grappoli.cli` (`read NOTES`); the pipeline is `map`
(Stage 1, arithmetic) then `characterise` (Stage 2, one model call per
region), with generation behind the single interface in `model`. The
reason this is a package rather than a bare script is pyproject.toml's
CPU-only torch pin: uv honours `[tool.uv.sources]` only for a package
project.
"""
