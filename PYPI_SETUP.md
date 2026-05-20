# PyPI publishing (one-time operator setup)

Releases run on tag push `v*` via [.github/workflows/release.yml](.github/workflows/release.yml).

## You do not "create a project" on PyPI first

PyPI no longer has a separate "register project" step. The project **`mapsnatch`** is created automatically on the **first successful upload** of a wheel/sdist (name must still be available on PyPI).

Check availability: https://pypi.org/project/mapsnatch/ — 404 means the name is free.

## Option A — Trusted publishing (OIDC, in use)

1. PyPI → **your account** → **Publishing** → **Add pending publisher**
   - PyPI project name: `mapsnatch`
   - Owner: `gavinc`
   - Repository: `mapsnatch`
   - Workflow: `release.yml`
   - Environment: `pypi`
2. GitHub → `gavinc/mapsnatch` → Environment **`pypi`** (no token secret required).
3. Push a release tag (see **Release** below).

## Option B — API token (fallback)

1. Create an API token at [pypi.org](https://pypi.org) → Account settings → API tokens.
2. GitHub → environment **`pypi`** → secret **`PYPI_API_TOKEN`**.
3. Add `password: ${{ secrets.PYPI_API_TOKEN }}` to the Publish step in `release.yml`.

Do **not** mix OIDC and token in `release.yml` unless you know which path you want.

## Release

```bash
git tag v0.1.0   # or next semver
git push origin v0.1.0
```

Watch **Actions → Release**, then:

```bash
pip install mapsnatch
mapsnatch --help
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Project does not exist" in PyPI UI | Normal before first upload — publish once via workflow or `twine upload`. |
| `403` / invalid token | Regenerate token; update `PYPI_API_TOKEN` on environment `pypi`. |
| `invalid-publisher` on OIDC | Add pending publisher on PyPI (account → Publishing); fields must match exactly. |
| Name already taken | Pick another PyPI name and change `name` in `pyproject.toml`. |
| Release workflow skipped | Tag must match `v*` (e.g. `v0.1.0`), not `0.1.0`. |
| Environment missing | Create **`pypi`** under Settings → Environments. |

## Local smoke test (optional)

```bash
pip install build twine
python -m build
# twine upload dist/*   # only if testing token locally; prefer CI tag push
```
