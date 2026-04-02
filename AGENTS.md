# Repository Guidelines

## Project Structure & Module Organization
This repository is currently in a bootstrap state: the working tree contains no application source, test suite, or build configuration yet. Keep the top level minimal and add code only when the structure is clear.

Recommended layout as the project grows:
- `src/` for application code
- `test/` or `tests/` for automated tests
- `docs/` for design notes and operational documentation
- `assets/` for static files such as sample data or diagrams

Use small, focused modules and group files by feature or pipeline stage rather than by generic utility buckets.

## Build, Test, and Development Commands
No build, test, or local run commands are defined in the current checkout. Before adding contributors, introduce a single documented entry point for each workflow and keep it stable.

Examples to add once tooling exists:
- `make test` to run the full test suite
- `make lint` to run formatting and static checks
- `make dev` to start the local development workflow

Document any new command in `README.md` when it is introduced.

## Coding Style & Naming Conventions
Because no formatter or linter is configured yet, keep style conservative and predictable:
- Use 4 spaces for indentation unless the chosen language ecosystem strongly prefers otherwise.
- Prefer descriptive file and module names such as `stream_parser.py` or `event_sink.ts`.
- Use `snake_case` for filenames, functions, and variables unless the language standard differs.
- Keep public interfaces narrow and avoid large multi-purpose modules.

Adopt an automated formatter and linter early, then treat their output as authoritative.

## Testing Guidelines
No test framework is configured yet. Add tests alongside the first production modules and keep naming aligned with the language toolchain, for example `test_stream_parser.py` or `stream-parser.test.ts`.

Every new feature or bug fix should include at least one automated test covering the expected behavior and one failure case where practical.

## Commit & Pull Request Guidelines
No Git history is available in this checkout, so there is no repository-specific commit convention to inherit yet. Start with short, imperative commit subjects such as `Add stream ingestion skeleton`.

For pull requests:
- Describe the change and its motivation
- Link the relevant issue or task when one exists
- List validation performed locally
- Include screenshots or logs only when they clarify behavior

Keep PRs small enough to review in one pass.
