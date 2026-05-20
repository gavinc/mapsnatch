# Contributing to MapSnatch

Thanks for helping improve bulk export for MindMeister users. This repo is the **open-source CLI**; the hosted product lives at [mapsnatch.com](https://mapsnatch.com).

## Before you start

- Read [README.md](./README.md) for usage and architecture
- Check [open issues](https://github.com/gavinc/mapsnatch/issues) and existing PRs
- For security issues, see [SECURITY.md](./SECURITY.md) — no public issues for vulnerabilities

## Development setup

```bash
git clone https://github.com/gavinc/mapsnatch.git
cd mapsnatch
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"   # or: pip install -e . && pip install pytest pytest-mock responses
```

Copy `.env.example` to `.env` for local runs. **Never commit real tokens.**

## Running tests

```bash
python -m pytest -v
```

All HTTP to MindMeister must be mocked in tests (`responses` or equivalent). No live API calls in CI or PRs.

## Pull request checklist

- [ ] Tests added or updated for behavior changes
- [ ] `python -m pytest -v` passes locally
- [ ] No secrets, tokens, or personal map data in the diff
- [ ] README or docstrings updated if user-facing behavior changed
- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, `test:`)

## Code style

- Python 3.9+ compatible
- Prefer clear names over clever one-liners
- Match existing patterns in `src/meister_export/`

## Scope we are likely to accept

- Bug fixes, better errors, format handling, test coverage
- Docs and examples
- Performance improvements that do not change trust boundaries

## Scope that needs discussion first

- New export formats (must be supported by MindMeister API for non-Business users)
- Breaking CLI flag or output layout changes
- License changes

Open a [feature request](https://github.com/gavinc/mapsnatch/issues/new?template=feature_request.yml) before large builds.

## Community

This project follows [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md). Be excellent to each other.
