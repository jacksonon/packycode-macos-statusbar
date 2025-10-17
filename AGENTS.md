# Repository Guidelines

## Project Structure & Module Organization
PackyCode is a single Python menu-bar app anchored in `main.py`, which defines `PackycodeStatusApp` and helpers for config persistence, API calls, and UI menus. Assets live in `assets/` (notably `icon.png`), while packaging scripts sit alongside the entry point: `build_app.sh`, `build.sh`, and `setup.py`. Runtime docs and screenshots are in `README.md`, `DOCS.md`, and `product.png`. User-specific configuration is written to `~/.packycode/config.json`; keep that path ignored from version control.

## Build, Test, and Development Commands
- `pip3 install -r requirements.txt` installs runtime dependencies (`rumps`, `requests`, `pyobjc`). Use a local virtual environment when iterating.
- `python3 main.py` launches the status bar app and streams status updates to the terminal.
- `bash build_app.sh [--clean|--open|--no-venv]` packages a macOS `.app`, recreating `.venv` when necessary.
- `bash build.sh` wipes `build/` and `dist/` before delegating to `build_app.sh`; run this before publishing artifacts.
- `python3 setup.py py2app` remains available if you need the raw py2app entry point for CI or custom packaging.

## Coding Style & Naming Conventions
Follow PEP 8: four-space indentation, snake_case for functions, and UPPER_SNAKE_CASE for constants (`CONFIG_DIR`, `ACCOUNT_ENV`). Keep localized UI strings in Chinese to match the current menu language. New modules should expose focused helpers (e.g., `fetch_usage()`), and multi-threaded updates must stay behind the existing `threading.RLock`. Shell scripts should remain POSIX Bash with `set -euo pipefail` at the top.

## Testing Guidelines
The project currently relies on manual verification. Run `python3 main.py`, walk through menu actions (refresh, token entry, account switching), and ensure API failures surface as menu error states rather than crashes. When adding automated coverage, place tests in `tests/` using `pytest`, name files `test_*.py`, and mock HTTP calls so contributors can execute `pytest` without live credentials.

## Commit & Pull Request Guidelines
History favors short imperative commits (`add github action`). Continue that style but add meaningful context, e.g., `add daily budget rollover handling`. Pull requests should summarize the user-visible change, list manual checks performed, and link PackyCode tracking issues. Add screenshots or console excerpts when tweaking menu text or build output, and flag any required config migrations or new secrets.

## Security & Configuration Tips
API tokens are stored in plaintext at `~/.packycode/config.json`, so scrub personal data from samples and logs. Never commit real credentials; use placeholders like `"<token>"`. Network-facing changes must document new domains or headers in `README.md` and note any additional environment variables reviewers need to test safely.
