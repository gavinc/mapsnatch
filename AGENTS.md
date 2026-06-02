# AGENTS.md

Guidance for AI coding assistants working on this repo.

## Issues-first workflow (mandatory)

**No ticket, no workee.** Do not implement features or bugfixes requested in chat until a tracking GitHub Issue exists.

| Request in chat | Agent action |
|-----------------|--------------|
| New feature | Create issue (`[feat]: …`) via `gh-ll issue create`, then branch |
| Bug / regression | Create issue (`[bug]: …`), then branch |
| Question / explanation only | Answer; no issue required |
| Docs typo (one line) | Fix directly; issue optional |

Before writing implementation code:

1. Confirm repo has a GitHub remote and `gh-ll` auth for the `gavinc` identity (**github-identity-management**).
2. Open or find the issue; note the number.
3. Branch name should include the issue number when practical (`feat/123-short-name`).
4. PR body must include `Fixes #N`.

**Exceptions** (no issue required):

- Operator explicitly says "skip issue" or "no ticket".
- One-line typos, comment-only edits, or doc fixes with no behavior change.
- Active production incident when the operator declares hotfix mode.

If the operator describes substantive work but no issue exists, **create the issue first**, paste the URL back, then proceed.

## Repository shape

```
src/meister_export/         Python package - the actual tool
  cli.py                    argparse entrypoint, `mapsnatch` console script
  client.py                 MindMeister API client (single token-bearing surface)
  exporter.py               format-specific export (md, pdf, etc.)
tests/                      pytest suite (test_cli.py, test_client.py, test_exporter.py)
docs/                       mkdocs source (architecture.md, api-limits.md, index.md)
security/semgrep/           project-specific Semgrep rules (token-leak guards)
scripts/owasp-gate.sh       local mirror of CI owasp-sast job
.github/workflows/          ci.yml (lint/test/owasp/secrets/audit), release.yml (PyPI), docs.yml (Pages)
PYPI_SETUP.md               operator wiring for the `pypi` environment + token / OIDC
REPO_SETTINGS.md            canonical record of GitHub-side controls
pyproject.toml              build config; dependencies pinned in requirements-prod.txt
```

## What you can change without asking

- Bug fixes inside `src/meister_export/` that are covered by an issue.
- New / expanded tests in `tests/`.
- Doc edits (`README.md`, `CONTRIBUTING.md`, `docs/`, `mkdocs.yml`).
- CI tuning that doesn't loosen security gates.
- Adding new Semgrep rules under `security/semgrep/mapsnatch.yml` to harden the token surface further.

## What needs operator approval

- Renaming or removing existing CLI flags (back-compat break for scripted users).
- Adding runtime dependencies beyond `requests`, `python-dotenv`, `tqdm` (the lean dep list is a feature - argue why before extending).
- Touching `.github/workflows/release.yml` (it has PyPI publish credentials).
- Switching the licence (currently AGPL-3.0-or-later; matched in README + `pyproject.toml`).
- Major architectural changes (e.g. swapping `requests` for `httpx`, async refactor).
- Loosening the OWASP SAST gate (no `--no-error`, no `nosemgrep:` comments without operator sign-off).

## Local verification before opening a PR

```bash
ruff check src tests                 # lint
ruff format --check src tests        # format
python -m pytest -v                  # unit tests
bash scripts/owasp-gate.sh           # Semgrep gate (Docker or pipx semgrep)
pip-audit -r requirements-prod.txt   # dependency CVE audit
```

CI runs the same checks (`lint-test` matrix on Python 3.9/3.11/3.12 + `owasp-sast` + `secret-scan` + `security-audit`). PRs can't merge to `main` until the aggregate `ci` job is green.

## Conventional commits

PR titles use [Conventional Commits](https://www.conventionalcommits.org/). Examples:

```
feat: add --format html exporter
fix: handle 429 with exponential backoff
docs: document MindMeister rate limits
chore: bump pinned requests to 2.31.1
ci: pin semgrep image to 1.122.0
refactor: extract HTTP retry helper from client.py
test: add fixture for missing-token error path
```

Breaking changes get a `!` suffix or a `BREAKING CHANGE:` footer. Release notes come from these on each tag.

## Style anchors

- **Python:** 3.9+ compatible. Stdlib + the three pinned runtime deps only. Async / new typing syntax allowed but verify 3.9 still parses.
- **Dependencies:** Production deps live in `requirements-prod.txt` (audited by CI). Dev deps live in `[project.optional-dependencies].dev` in `pyproject.toml`.
- **Linting:** `ruff` is the source of truth - both `ruff check` and `ruff format --check` must pass.
- **MindMeister token:** Read from `MINDMEISTER_API_TOKEN` env var or `--token` CLI flag. **Never** `print()`, `log`, or interpolate into f-strings outside the `Authorization` header construction. The Semgrep rules in `security/semgrep/mapsnatch.yml` enforce this and **will block CI** on violations.
- **HTTP errors:** Let `client.py` map them to the project's exception hierarchy. Don't leak raw `requests.exceptions.*` to the CLI layer.

## Where the brand canon lives

- `README.md` - user-facing pitch, install, CLI usage.
- `AGENTS.md` (this file) - agent-facing rules.
- `CONTRIBUTING.md` - human contributor workflow (issue → branch → PR → review).
- `SECURITY.md` - private vulnerability disclosure path.
- `PYPI_SETUP.md` / `REPO_SETTINGS.md` - operator-only setup + canonical settings record.
- `docs/` (mkdocs site) - architecture deep-dives, API limit walkthrough, longer-form contributor docs.

Update all relevant files when changing the area they cover. Don't put policy in one that belongs in another.
